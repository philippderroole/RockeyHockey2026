const express = require('express');
const rpio = require('rpio');

const app = express();

const PORT = 4321;

rpio.init({mapping: 'gpio'});
rpio.open(5, rpio.INPUT);
rpio.open(6, rpio.INPUT);

app.use('/resources', express.static('resources'));
app.use('/script', express.static('script'));
app.use('/style', express.static('style'));

app.get('/', (req, res) => {
    res.sendFile('index.html', { root: __dirname });
});

app.get('/state', (req, res) => {
    res.json({"gpio5": rpio.read(5), "gpio6": rpio.read(6)});
});

app.listen(PORT, () => console.log("Server listening on port", PORT));