const cpu = document.querySelector("#cpu_usage");
const mem = document.querySelector("#memory_usage");
const mem_total = document.querySelector("#memory_total");
const disk = document.querySelector("#disk_usage");
const disk_total = document.querySelector("#disk_total");
const power = document.querySelector("#power_draw");


function update() {
  fetch('/api/stats')
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

  for (let status of document.querySelectorAll('.status')) {
    const url = status.getAttribute('data-url');
    fetch(url)
      .then(response => {
        if (response.ok) {
          status.classList.remove('error');
          status.classList.add('ok');
        } else {
          status.classList.remove('ok');
          status.classList.add('error');
        }
      }).catch(error => {
        status.classList.remove('ok');
        status.classList.add('error');
      });
  }
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

update();
setInterval(update, 2000);