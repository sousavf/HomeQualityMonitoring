#include "dht.h"
#include "MQ135.h"

MQ135 gasSensor = MQ135(0);
dht DHT;

#define RLOAD 1.0
#define DHT11_PIN 2
#define LIGHT_SENSOR_PIN A1

#define SENSOR_ID "5ND1HU"

void setup()
{
	Serial.begin(115200);
}

void loop()
{
	int chk = DHT.read11(DHT11_PIN);

	float raw = gasSensor.getResistance();
	float rzero = gasSensor.getRZero();
	float ppm = gasSensor.getPPM();

	float light = analogRead(LIGHT_SENSOR_PIN);
	
	Serial.print("data");
	Serial.print(";");
	Serial.print(SENSOR_ID);
	Serial.print(";");
	Serial.print(raw);
	Serial.print(";");
	Serial.print(rzero);
	Serial.print(";");
	Serial.print(ppm);
	Serial.print(";");
	Serial.print(light);
	Serial.print(";");
	Serial.print(DHT.humidity);
	Serial.print(";");
	Serial.print(DHT.temperature);
	Serial.print(";");
  
	Serial.println();
	delay(30000);
}
