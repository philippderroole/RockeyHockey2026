const express = require('express');
const rpio = require('rpio');
const { spawn } = require('node:child_process');

const app = express();

const PORT = 4321;

let playerScore = 0;
let botScore    = 0;

let gameRunning = false;

const botGoalPin    = 5;
const playerGoalPin = 6;

rpio.init({mapping: 'gpio'});
rpio.open(botGoalPin, rpio.INPUT);
rpio.open(playerGoalPin, rpio.INPUT);
const ledDriver = spawn('python', ['ledDriver/driver.py'])

app.use("/resources", express.static("resources"));
app.use("/script", express.static("script"));
app.use("/style", express.static("style"));

app.get("/", (req, res) => {
  res.sendFile("index.html", { root: __dirname });
});

function onGoalSensor(pin) {
    rpio.poll(botGoalPin, null);
    rpio.poll(playerGoalPin, null);

    let pointsToAdd = 1;
    if (eventActive) {
        pointsToAdd = 2;
    }
    if (rpio.read(pin)) { // only give points when puck entered light barrier
        if (pin === playerGoalPin)
            botScore += pointsToAdd;
        else if (pin == botGoalPin)
            playerScore += pointsToAdd;
    }
    
    setTimeout(() => {
        if (gameRunning === true) {
            rpio.poll(botGoalPin, onGoalSensor);
            rpio.poll(playerGoalPin, onGoalSensor);
        }
    }, 1000);
}

app.get('/event/start', (req, res) => {
    eventActive = true;
    res.send("event started");
});
app.get('/event/stop', (req, res) => {
    eventActive = true;
    res.send("event stopped");
});
app.get('/state', (req, res) => {
    res.json({"playerScore": playerScore, "botScore": botScore});
});

let animationInterval;

app.get('/animation/:color', (req, res) => {
    clearInterval(animationInterval);
    
    const numLeds = 215;
    const RED  = [100, 0,   0];
    const BLUE = [0,   0, 100];
    const OFF  = [0,   0,   0];
    
    let color;
    if (req.params.color === "red")
        color = RED;
    else if (req.params.color === "blue")
        color = BLUE;
    else
        color = OFF;

    let leds = [];
    leds = Array(numLeds).fill(OFF)
    for (let i = 0; i < 18; i++)
        leds = leds.concat([color,color,color,color,OFF,OFF,OFF,OFF,OFF,OFF,OFF,OFF])
    leds = leds.concat(Array(numLeds).fill(OFF))
    
    animationInterval = setInterval(() => {
        let frame = leds.slice(0,numLeds).reverse();
        if (frame.length < numLeds) {
            clearInterval(animationInterval);
        }
        else {
            ledDriver.stdin.write(frame.join(";") + "\n");
            leds.shift();
            leds.shift();
        }
    }, 22);
    
    res.json({"animation": "ok"});
});

/// Set scores to 0.
app.get('/resetScores', (req, res) => { playerScore = botScore = 0; res.send("scores reset.") });
/// Start counting scores.
app.get('/start', (req, res) => { gameRunning = true; rpio.poll(botGoalPin, onGoalSensor); rpio.poll(playerGoalPin, onGoalSensor); res.send("started."); });
/// Stop counting scores.
app.get('/stop' , (req, res) => { gameRunning = false; rpio.poll(botGoalPin, null);         rpio.poll(playerGoalPin, null);         res.send("stopped.");});

/// Set scores to 0.
app.get('/resetScores', (req, res) => { playerScore = botScore = 0; res.send("scores reset.") });
/// Start counting scores.
app.get('/start', (req, res) => { rpio.poll(botGoalPin, onGoalSensor); rpio.poll(playerGoalPin, onGoalSensor); res.send("started."); });
/// Stop counting scores.
app.get('/stop' , (req, res) => { rpio.poll(botGoalPin, null);         rpio.poll(playerGoalPin, null);         res.send("stopped.");});

app.listen(PORT, () => console.log("Server listening on port", PORT));
