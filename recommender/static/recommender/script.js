(function () {
  var introScreen = document.getElementById('introScreen');
  var trialScreen = document.getElementById('trialScreen');
  var doneScreen = document.getElementById('doneScreen');
  var startBtn = document.getElementById('startBtn');
  var progressText = document.getElementById('progressText');
  var taskBanner = document.getElementById('taskBanner');
  var timerText = document.getElementById('timerText');
  var grid = document.getElementById('grid');
  var ratingPanel = document.getElementById('ratingPanel');
  var relevanceScale = document.getElementById('relevanceScale');
  var easeScale = document.getElementById('easeScale');
  var nextRoundBtn = document.getElementById('nextRoundBtn');
  var nameInput = document.getElementById('participantName');

  var sessionId = null, modeOrder = [], targets = {};
  var roundIndex = 0;
  var startTime = null, timerInterval = null;
  var targetFound = false;
  var relevanceVal = null, easeVal = null;

  // Pichla naam pre-fill kar do (convenience ke liye), lekin field hamesha editable rehta hai
  var lastName = localStorage.getItem('participant_name');
  if (lastName) { nameInput.value = lastName; }

  function buildScale(container, onPick) {
    container.innerHTML = '';
    for (var i = 1; i <= 5; i++) {
      (function (n) {
        var b = document.createElement('button');
        b.type = 'button'; b.textContent = n; b.setAttribute('aria-pressed', 'false');
        b.addEventListener('click', function () {
          Array.prototype.forEach.call(container.children, function (c) { c.setAttribute('aria-pressed', 'false'); });
          b.setAttribute('aria-pressed', 'true');
          onPick(n);
        });
        container.appendChild(b);
      })(i);
    }
  }
  buildScale(relevanceScale, function (n) { relevanceVal = n; checkReady(); });
  buildScale(easeScale, function (n) { easeVal = n; checkReady(); });
  function checkReady() { nextRoundBtn.disabled = !(relevanceVal && easeVal); }

  startBtn.addEventListener('click', function () {
    var nameToUse = nameInput.value.trim();
    if (!nameToUse) { alert('Apna naam daalo pehle'); return; }
    localStorage.setItem('participant_name', nameToUse);

    fetch('/api/session/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: nameToUse,
        age_range: document.getElementById('ageRange').value,
        web_familiarity: document.getElementById('webFamiliarity').value
      })
    }).then(function (r) { return r.json(); }).then(function (data) {
      sessionId = data.session_id;
      modeOrder = data.mode_order;
      targets = data.targets;
      roundIndex = 0;
      introScreen.classList.add('hidden');
      trialScreen.classList.remove('hidden');
      runRound();
    });
  });

  function runRound() {
    var mode = modeOrder[roundIndex];
    var target = targets[mode];
    targetFound = false;
    relevanceVal = null; easeVal = null;
    ratingPanel.classList.add('hidden');
    Array.prototype.forEach.call(relevanceScale.children, function (c) { c.setAttribute('aria-pressed', 'false'); });
    Array.prototype.forEach.call(easeScale.children, function (c) { c.setAttribute('aria-pressed', 'false'); });
    checkReady();

    progressText.textContent = 'Round ' + (roundIndex + 1) + ' of ' + modeOrder.length;
    taskBanner.innerHTML = '🎯 Find something in <span class="target-word">' + target + '</span>';

    var url = mode === 'static' ? '/api/items'
      : mode === 'random' ? '/api/items/random'
      : '/api/recommendations?session_id=' + encodeURIComponent(sessionId);

    grid.innerHTML = '<p style="color:var(--muted);font-size:13px;">Loading…</p>';
    fetch(url).then(function (r) { return r.json(); }).then(function (items) {
      renderGrid(items, mode, target);
      startTimer();
    });
  }

  function renderGrid(items, mode, target) {
    grid.innerHTML = '';
    items.forEach(function (item) {
      var el = document.createElement('div');
      el.className = 'card';
      el.innerHTML = '<span class="cat-tag">' + item.category + '</span><h3>' + item.title + '</h3><p>' + item.body + '</p>';
      el.addEventListener('click', function () {
          el.classList.add('clicked');
           handleClick(item, mode, target); 
          });
      grid.appendChild(el);
    });
  }

  function startTimer() {
    startTime = performance.now();
    clearInterval(timerInterval);
    timerInterval = setInterval(function () {
      var elapsed = (performance.now() - startTime) / 1000;
      timerText.textContent = 'Time: ' + elapsed.toFixed(1) + 's';
    }, 100);
  }

  function handleClick(item, mode, target) {
    if (targetFound) return;
    var isTarget = item.category === target;
    var elapsedMs = Math.round(performance.now() - startTime);

    fetch('/api/click', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId, mode: mode, item_id: item.id,
        is_target: isTarget, time_taken_ms: isTarget ? elapsedMs : null
      })
    });

    if (isTarget) {
      targetFound = true;
      clearInterval(timerInterval);
      ratingPanel.classList.remove('hidden');
    }
  }

  nextRoundBtn.addEventListener('click', function () {
    var mode = modeOrder[roundIndex];
    fetch('/api/rating', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, mode: mode, relevance: relevanceVal, ease: easeVal })
    }).then(function () {
      roundIndex++;
      if (roundIndex < modeOrder.length) {
        runRound();
      } else {
        trialScreen.classList.add('hidden');
        doneScreen.classList.remove('hidden');
      }
    });
  });

  function exportCSV(url, filename, columns) {
    fetch(url).then(function (r) { return r.json(); }).then(function (rows) {
      if (!rows.length) { alert('No data yet.'); return; }
      var csv = [columns.join(',')];
      rows.forEach(function (row) {
        csv.push(columns.map(function (c) { return JSON.stringify(row[c] !== undefined ? row[c] : ''); }).join(','));
      });
      var blob = new Blob([csv.join('\n')], { type: 'text/csv' });
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob); link.download = filename;
      document.body.appendChild(link); link.click(); document.body.removeChild(link);
    });
  }

  document.getElementById('exportClicksBtn').addEventListener('click', function () {
    exportCSV('/api/log', 'clicks.csv', ['session_id', 'mode', 'item_id', 'category', 'is_target', 'time_taken_ms', 'created_at']);
  });
  document.getElementById('exportRatingsBtn').addEventListener('click', function () {
    exportCSV('/api/ratings', 'ratings.csv', ['session_id', 'mode', 'relevance', 'ease', 'created_at']);
  });
  document.getElementById('restartBtn').addEventListener('click', function () {
    doneScreen.classList.add('hidden');
    nameInput.value = '';               // agle participant ke liye field khaali kar do
    introScreen.classList.remove('hidden');
  });
})();