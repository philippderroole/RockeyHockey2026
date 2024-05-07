
setInterval(() => {
    fetch("state").then((res) => res.json().then((json) => {
        gpio5.value = json.gpio5;
        gpio6.value = json.gpio6;
    }))
}, 500);