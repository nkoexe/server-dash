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
}


document.querySelector("#exit_actions").onclick = () => {
  menu.classList.remove("visible");
}



function update_system() {
  fetch('/api/system')
    .then(response => response.json())
    .then(data => {
      cpu.textContent = data.cpu;
      graphs[0].addValue(data.cpu);
      mem.textContent = (data.memory.used / 1073741824).toFixed(1);
      mem_total.textContent = (data.memory.total / 1073741824).toFixed(1);
      graphs[1].addValue((data.memory.used / data.memory.total) * 100);
      disk.textContent = (data.disk.used / 1073741824).toFixed(1);
      disk_total.textContent = (data.disk.total / 1073741824).toFixed(0);
      graphs[2].addValue((data.disk.used / data.disk.total) * 100);
      if (typeof data.power === 'number') {
        power.textContent = data.power.toFixed(1);
        graphs[3].addValue((data.power / 20) * 100);
      } else {
        power.textContent = data.power;
      }
    });
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
    });
}


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

        const name = document.createElement('div');
        name.className = 'docker_name';
        name.textContent = container.name;

        const status = document.createElement('div');
        status.className = 'docker_status secondary';
        status.textContent = container.status;

        item.appendChild(indicator);
        item.appendChild(name);
        item.appendChild(status);
        docker_list.appendChild(item);
      });
    })
    .catch(error => {
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
}

let graphs = [];
const graph_x_interval = 40;


function addToGraph(ctx, y, prev_y) {
  const imageData = ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.putImageData(imageData, -graph_x_interval, 0);

  let x = ctx.canvas.width;
  let prev_x = x - graph_x_interval;
  ctx.beginPath();
  ctx.strokeStyle = "white";
  ctx.moveTo(prev_x, prev_y);
  ctx.bezierCurveTo(x - graph_x_interval / 2, prev_y - 10, x - graph_x_interval / 2, y + 10, x, y);
  ctx.stroke();
  ctx.lineTo(x, ctx.canvas.height);
  ctx.lineTo(prev_x, ctx.canvas.height);
  ctx.lineTo(prev_x, prev_y);
  ctx.fillStyle = "rgba(255, 255, 255, 0.2)";
  ctx.fill();
  ctx.closePath();

  ctx.prev_y = y;
}


document.querySelectorAll(".graph").forEach(graph => {
  graph = graph.getContext("2d", { willReadFrequently: true });
  graph.prev_y = graph.canvas.height;
  graph.addValue = (value) => {
    value = (graph.canvas.height - 10) - ((value / 100) * (graph.canvas.height - 10));
    addToGraph(graph, value, graph.prev_y);
  }
  graphs.push(graph);
});



update_system();
setInterval(update_system, 2000);

update_websites();
setInterval(update_websites, 30000);

update_docker();
setInterval(update_docker, 10000);