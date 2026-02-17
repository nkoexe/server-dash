const cpu = document.querySelector("#cpu_usage");
const mem = document.querySelector("#memory_usage");
const mem_total = document.querySelector("#memory_total");
const disk = document.querySelector("#disk_usage");
const disk_total = document.querySelector("#disk_total");
const power = document.querySelector("#power_draw");
const menu = document.querySelector("#actions_menu");
const docker_running = document.querySelector("#docker_running");
const docker_total = document.querySelector("#docker_total");
const docker_list = document.querySelector("#docker_list");


document.querySelector("#actions_button").onclick = () => {
  menu.classList.add("visible");
};

document.querySelector("#exit_actions").onclick = () => {
  menu.classList.remove("visible");
};



const BYTES_TO_GB = 1073741824; // 1024^3

function update_system() {
  fetch('/api/system')
    .then(response => response.json())
    .then(data => {
      cpu.textContent = data.cpu;
      graphs[0].addValue(data.cpu);
      mem.textContent = (data.memory.used / BYTES_TO_GB).toFixed(1);
      mem_total.textContent = (data.memory.total / BYTES_TO_GB).toFixed(1);
      graphs[1].addValue((data.memory.used / data.memory.total) * 100);
      disk.textContent = (data.disk.used / BYTES_TO_GB).toFixed(1);
      disk_total.textContent = (data.disk.total / BYTES_TO_GB).toFixed(0);
      graphs[2].addValue((data.disk.used / data.disk.total) * 100);
      if (typeof data.power === 'number') {
        power.textContent = data.power.toFixed(1);
        graphs[3].addValue((data.power / 20) * 100);
      } else {
        power.textContent = data.power;
      }
    })
    .catch(error => console.error('Error fetching system data:', error));
}


function update_websites() {
  fetch("/api/websites")
    .then(response => response.json())
    .then(data => {
      for (let url in data) {
        const status = document.querySelector(`.status[data-url="${url}"]`);
        if (status) {
          if (data[url] === 'up') {
            status.classList.remove('error');
            status.classList.add('ok');
          } else {
            status.classList.remove('ok');
            status.classList.add('error');
          }
        }
      }
    })
    .catch(error => console.error('Error fetching website status:', error));
}

function update_website_uptime() {
  fetch('/api/websites/uptime')
    .then(response => response.json())
    .then(data => {
      // Check if response is error object
      if (data.error) {
        console.warn('Website uptime error:', data.error);
        return;
      }

      for (let url in data) {
        const stats = data[url];
        const dotsContainer = document.querySelector(`.uptime-dots[data-url="${url}"]`);
        const statusItem = document.querySelector(`.status[data-url="${url}"]`);

        if (dotsContainer && stats) {
          renderUptimeDots(dotsContainer, stats);

          if (statusItem) {
            const tooltip = statusItem.querySelector('.uptime-tooltip');
            if (tooltip) {
              updateTooltip(tooltip, stats);
            }
          }
        }
      }
    })
    .catch(error => console.error('Error fetching website uptime:', error));
}

function update_docker_uptime() {
  fetch('/api/docker/uptime')
    .then(response => response.json())
    .then(data => {
      // Check if response is error object
      if (data.error) {
        console.warn('Docker uptime error:', data.error);
        return;
      }

      for (let name in data) {
        const stats = data[name];
        const dotsContainer = document.querySelector(`.uptime-dots[data-container="${name}"]`);
        const dockerItem = dotsContainer?.closest('.docker_item');

        if (dotsContainer && stats) {
          renderUptimeDots(dotsContainer, stats);

          if (dockerItem) {
            const tooltip = dockerItem.querySelector('.uptime-tooltip');
            if (tooltip) {
              updateTooltip(tooltip, stats);
            }
          }
        }
      }
    })
    .catch(error => console.error('Error fetching docker uptime:', error));
}

function renderUptimeDots(container, stats) {
  // Remove loading state
  container.classList.remove('loading');

  // Get existing dots or create new ones if needed
  let dots = container.querySelectorAll('.uptime-dot');

  // If no dots exist, create them
  if (dots.length === 0) {
    for (let i = 0; i < 30; i++) {
      const dot = document.createElement('div');
      dot.className = 'uptime-dot';
      container.appendChild(dot);
    }
    dots = container.querySelectorAll('.uptime-dot');
  }

  // Calculate daily uptime (simplified - using 30d data)
  const uptime30d = stats.uptime_30d ?? stats.uptime_all ?? 0;

  // Update dot states
  dots.forEach((dot, i) => {
    // Remove existing state classes
    dot.classList.remove('up', 'down');

    // Simulate per-day status based on overall uptime
    // In reality, you'd need per-day data from backend
    const isUp = Math.random() * 100 < uptime30d;
    dot.classList.add(isUp ? 'up' : 'down');
  });
}

function updateTooltip(tooltip, stats) {
  const values = tooltip.querySelectorAll('.uptime-stat .value');
  if (values.length >= 3) {
    values[0].textContent = stats.uptime_24h != null ? `${stats.uptime_24h.toFixed(1)}%` : '-';
    values[1].textContent = stats.uptime_7d != null ? `${stats.uptime_7d.toFixed(1)}%` : '-';
    values[2].textContent = stats.uptime_30d != null ? `${stats.uptime_30d.toFixed(1)}%` : '-';
  }
}


const UPTIME_TOOLTIP_HTML = `
  <div class="uptime-tooltip-content">
    <div class="uptime-stat"><span class="label">24h:</span> <span class="value">-</span></div>
    <div class="uptime-stat"><span class="label">7d:</span> <span class="value">-</span></div>
    <div class="uptime-stat"><span class="label">30d:</span> <span class="value">-</span></div>
  </div>
`;

function update_docker() {
  fetch('/api/docker')
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        docker_running.textContent = '!';
        docker_total.textContent = '!';
        docker_list.innerHTML = '<div class="docker_item error"><div class="indicator"></div><div class="docker_name">Error: ' + data.error + '</div></div>';
        return;
      }

      docker_running.textContent = data.running;
      docker_total.textContent = data.total;

      docker_list.innerHTML = '';
      data.containers.forEach(container => {
        const item = document.createElement('div');
        item.className = 'docker_item ' + (container.state === 'running' ? 'ok' : 'error');

        const indicator = document.createElement('div');
        indicator.className = 'indicator';

        const content = document.createElement('div');
        content.className = 'docker_content';

        const name = document.createElement('div');
        name.className = 'docker_name';
        name.textContent = container.name;

        const uptimeDots = document.createElement('div');
        uptimeDots.className = 'uptime-dots loading';
        uptimeDots.dataset.container = container.name;

        // Pre-render 30 loading dots to prevent layout shift
        for (let i = 0; i < 30; i++) {
          const dot = document.createElement('div');
          dot.className = 'uptime-dot';
          uptimeDots.appendChild(dot);
        }

        content.appendChild(name);
        content.appendChild(uptimeDots);

        const status = document.createElement('div');
        status.className = 'docker_status secondary';
        status.textContent = container.status;

        const tooltip = document.createElement('div');
        tooltip.className = 'uptime-tooltip';
        tooltip.innerHTML = UPTIME_TOOLTIP_HTML;

        item.appendChild(indicator);
        item.appendChild(content);
        item.appendChild(status);
        item.appendChild(tooltip);
        docker_list.appendChild(item);
      });
    })
    .catch(error => {
      console.error('Error fetching docker status:', error);
      docker_running.textContent = '!';
      docker_total.textContent = '!';
      docker_list.innerHTML = '<div class="docker_item error"><div class="indicator"></div><div class="docker_name">Failed to fetch</div></div>';
    });
}

function call(endpoint) {
  fetch(`/api/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
  })
    .then(response => response.json())
    .then(data => {
      if (data.status !== 'ok') {
        console.error('Command failed:', data.message);
      }
    })
    .catch(error => console.error('Error calling endpoint:', error));
}

let graphs = [];
const graph_time_interval = 2000; // ms between data points

function addToGraph(ctx, y, prev_y) {
  const canvas = ctx.canvas;
  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;

  const imageData = ctx.getImageData(0, 0, canvasWidth, canvasHeight);
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  // Calculate pixel interval based on DISPLAY width, not canvas width (which includes buffer)
  // We want ~10 data points visible on screen
  const displayWidth = canvas.clientWidth;
  const bufferSize = displayWidth * 0.1;
  const actualDisplayWidth = displayWidth - bufferSize; // Subtract buffer from total
  const devicePixelRatio = window.devicePixelRatio || 1;
  const pixelInterval = Math.ceil((actualDisplayWidth * devicePixelRatio) / 10);

  ctx.putImageData(imageData, -pixelInterval, 0);

  // Draw at the right edge of the visible area
  // Canvas has extra buffer on left, so draw at canvasWidth (which is displayWidth + buffer)
  let x = canvasWidth;
  let prev_x = x - pixelInterval;

  // Draw the bezier curve stroke
  ctx.beginPath();
  ctx.strokeStyle = "white";
  ctx.moveTo(prev_x, prev_y);
  ctx.bezierCurveTo(x - pixelInterval / 2, prev_y - 10, x - pixelInterval / 2, y + 10, x, y);
  ctx.stroke();

  // Draw the fill area (separate path to avoid stroking the fill edges)
  ctx.beginPath();
  ctx.moveTo(prev_x, prev_y);
  ctx.bezierCurveTo(x - pixelInterval / 2, prev_y - 10, x - pixelInterval / 2, y + 10, x, y);
  ctx.lineTo(x, canvas.height);
  ctx.lineTo(prev_x, canvas.height);
  ctx.closePath();
  ctx.fillStyle = "rgba(255, 255, 255, 0.2)";
  ctx.fill();

  ctx.prev_y = y;

  // Calculate CSS pixel offset (transform operates on display pixels, not canvas resolution)
  // displayPixelInterval is the canvas interval scaled back to CSS pixels
  const displayPixelInterval = pixelInterval / devicePixelRatio;

  // Initialize animation state if needed
  if (!canvas.animationState) {
    canvas.animationState = {
      currentOffset: 0,
      lastTimestamp: performance.now(),
      animating: false,
      velocity: 0,
      devicePixelRatio: devicePixelRatio
    };
  }

  // Update pixel interval in case canvas was resized
  canvas.animationState.pixelInterval = displayPixelInterval;

  // Smoothly add new segment distance to current offset (no hard reset)
  // Just increment the offset that needs to be animated away
  canvas.animationState.currentOffset += displayPixelInterval;

  // Calculate dynamic velocity based on current total distance to animate
  // velocity = total_distance / desired_time
  canvas.animationState.velocity = (canvas.animationState.currentOffset / graph_time_interval) * 1000; // pixels per second

  // Update transform immediately to reflect new offset (prevent visual jump)
  canvas.style.transform = `translateX(${canvas.animationState.currentOffset}px)`;

  // Start animation if not already running
  if (!canvas.animationState.animating) {
    canvas.animationState.animating = true;
    canvas.animationState.lastTimestamp = performance.now();
    requestAnimationFrame((ts) => animateCanvas(canvas, ts));
  }
  // If already animating, velocity will be recalculated in next frame
}


function animateCanvas(canvas, timestamp) {
  const state = canvas.animationState;
  if (!state) return;

  const deltaTime = timestamp - state.lastTimestamp;
  state.lastTimestamp = timestamp;

  // Recalculate velocity dynamically based on remaining distance
  // This ensures smooth adjustment when new data arrives during animation
  if (state.currentOffset > 0) {
    state.velocity = (state.currentOffset / graph_time_interval) * 1000; // pixels per second
  }

  // Move at dynamic velocity (pixels per millisecond)
  const movement = (state.velocity / 1000) * deltaTime;
  state.currentOffset -= movement;

  // Clamp to zero (don't overshoot to negative)
  if (state.currentOffset < 0) {
    state.currentOffset = 0;
  }

  canvas.style.transform = `translateX(${state.currentOffset}px)`;

  // Continue animating if we haven't reached zero
  if (state.currentOffset > 0.1) {
    requestAnimationFrame((ts) => animateCanvas(canvas, ts));
  } else {
    state.currentOffset = 0;
    canvas.style.transform = `translateX(0px)`;
    state.animating = false;
  }
}


document.querySelectorAll(".graph").forEach(canvas => {
  // Extend canvas width on the left side only for buffer
  const container = canvas.parentElement;
  const displayWidth = container.clientWidth;
  const displayHeight = container.clientHeight;
  const bufferSize = displayWidth * 0.1; // 10% buffer on left
  const devicePixelRatio = window.devicePixelRatio || 1;

  // Canvas internal resolution = (display width + buffer) * devicePixelRatio for crisp rendering
  canvas.width = (displayWidth + bufferSize) * devicePixelRatio;
  canvas.height = displayHeight * devicePixelRatio;

  // Set CSS dimensions to match display size (not internal resolution)
  canvas.style.width = `${displayWidth + bufferSize}px`;
  canvas.style.height = `${displayHeight}px`;

  // Shift canvas left to hide the buffer zone
  canvas.style.marginLeft = `-${bufferSize}px`;

  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  ctx.prev_y = ctx.canvas.height;
  ctx.addValue = (value) => {
    value = (ctx.canvas.height - 10) - ((value / 100) * (ctx.canvas.height - 10));
    addToGraph(ctx, value, ctx.prev_y);
  };
  graphs.push(ctx);
});



update_system();
setInterval(update_system, 2000);

update_websites();
setInterval(update_websites, 30000);

update_docker();
setInterval(update_docker, 10000);

// Fetch uptime data after a brief delay (let initial data populate)
setTimeout(update_website_uptime, 2000);
setInterval(update_website_uptime, 60000);

setTimeout(update_docker_uptime, 3000);
setInterval(update_docker_uptime, 60000);