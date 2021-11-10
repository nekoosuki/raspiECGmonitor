const aliyunIot = require('aliyun-iot-device-sdk');
const deviceConfig = require('./device_id_password.json');

const device = aliyunIot.device(deviceConfig);
const fs = require("fs");
var seq = -1;
var count = -1;
device.on('connect', () => {
  console.log('Connect successfully!');
  console.log('Post properties every 1 seconds...');
  setInterval(() => { 
    try
    {
      var f = fs.readFileSync("/home/pi/heartpro/data.txt");
      f = f.toString();
      f = f.split("\n");
      var c = Number(f[0]);
      var hr = Number(f[1]);
      var t = f[2].split(",");
      var s = Number(f[3]);
      var tem = Number(f[4]);
      var hum = Number(f[5]);
      var gas = Number(f[6]);
      
      while(seq == s || isNaN(s))
      {
        f = fs.readFileSync("/home/pi/heartpro/data.txt");
        f = f.toString();
        f = f.split("\n");
        var s = Number(f[3]);
      }
      
      seq = s;

      for (var i = 0; i < t.length; i++)
      { 
        t[i] = Number(t[i]);
      }
      const params = {
        State: c,
        HeartRate: hr,
        Tick: t,
        Temperature: tem,
        Humidity: hum,
        Gas: gas
      };
      console.log("seq: " + seq + "   " + "count:" + ++count);
      console.log(`Post properties: ${JSON.stringify(params)}`);
      device.postProps(params);
    }
    catch(err)
    {
      console.log(err.stack);
    }
  }, 1000);
  
  device.serve('property/set', (data) => {
    console.log('Received a message: ', JSON.stringify(data));
  });
});

device.on('error', err => {
  console.error(err);
});
