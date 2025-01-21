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
      mem.textContent = (data.memory.used / 1073741824).toFixed(1);
      mem_total.textContent = (data.memory.total / 1073741824).toFixed(1);
      disk.textContent = (data.disk.used / 1073741824).toFixed(1);
      disk_total.textContent = (data.disk.total / 1073741824).toFixed(0);
      power.textContent = data.power.toFixed(1);
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

update();
setInterval(update, 5000);





function call(endpoint) {
  fetch(`/api/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
  })
}