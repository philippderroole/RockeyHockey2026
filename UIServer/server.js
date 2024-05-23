<<<<<<< HEAD
const express = require("express");
// const rpio = require('rpio');
=======
const express = require('express');
const rpio = require('rpio');
const { spawn } = require('node:child_process');
>>>>>>> 2ce63d0613718ba0c5390305b54410bcbe054bd4

const app = express();

const PORT = 4321;

<<<<<<< HEAD
// rpio.init({mapping: 'gpio'});
// rpio.open(5, rpio.INPUT);
// rpio.open(6, rpio.INPUT);
=======
rpio.init({mapping: 'gpio'});
rpio.open(5, rpio.INPUT);
rpio.open(6, rpio.INPUT);
const ledDriver = spawn('python', ['ledDriver/driver.py'])
>>>>>>> 2ce63d0613718ba0c5390305b54410bcbe054bd4

app.use("/resources", express.static("resources"));
app.use("/script", express.static("script"));
app.use("/style", express.static("style"));

app.get("/", (req, res) => {
  res.sendFile("index.html", { root: __dirname });
});

// app.get('/state', (req, res) => {
//     res.json({"gpio5": rpio.read(5), "gpio6": rpio.read(6)});
// });

<<<<<<< HEAD
=======
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

>>>>>>> 2ce63d0613718ba0c5390305b54410bcbe054bd4
app.listen(PORT, () => console.log("Server listening on port", PORT));
