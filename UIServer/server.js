const express = require('express');
const rpio = require('rpio');
const { spawn } = require('node:child_process');

const app = express();

const PORT = 4321;

rpio.init({mapping: 'gpio'});
rpio.open(5, rpio.INPUT);
rpio.open(6, rpio.INPUT);
const ledDriver = spawn('python', ['ledDriver/driver.py'])

app.use('/resources', express.static('resources'));
app.use('/script', express.static('script'));
app.use('/style', express.static('style'));

app.get('/', (req, res) => {
    res.sendFile('index.html', { root: __dirname });
});

app.get('/state', (req, res) => {
    res.json({"gpio5": rpio.read(5), "gpio6": rpio.read(6)});
});

let counter = 0;
let animationInterval;

app.get('/animation', (req, res) => {
    clearInterval(animationInterval);
    counter = 0;
    animationInterval = setInterval(() => {
        if (counter == 200) {
            counter = 0;
            clearInterval(animationInterval);
        } else {
            ledDriver.stdin.write("0,0,0;".repeat(counter) + "0,0,255\n");
            counter++;
        }
    }, 15);
    
    res.json({"animation": "ok"});
});

app.listen(PORT, () => console.log("Server listening on port", PORT));
