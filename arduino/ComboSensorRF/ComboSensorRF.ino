#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "dht.h"
#include "MQ135.h"

RF24 radio(9,10);

MQ135 gasSensor = MQ135(0);
dht DHT;

// Radio pipe addresses for the 2 nodes to communicate.
const uint64_t pipes[2] = { 0xF0F0F0F0E1LL, 0xF0F0F0F0D2LL };

const int max_payload_size = 64;

char receive_payload[max_payload_size+1]; // +1 to allow room for a terminating NULL char

#define DHT11_PIN 2
#define LIGHT_SENSOR_PIN A1

void setup(void)
{
  Serial.begin(115200);
  radio.begin();
  radio.enableDynamicPayloads();
  radio.setRetries(5,15);
  radio.openWritingPipe(pipes[0]);
  radio.openReadingPipe(1,pipes[1]);
  radio.startListening();
  radio.printDetails();
}


void loop(void)
{
  int chk = DHT.read11(DHT11_PIN);
	float rawGas = gasSensor.getResistance();
	float rawLight = analogRead(LIGHT_SENSOR_PIN);
  float rawHumidity = DHT.humidity;
  float rawTemperature = DHT.temperature;

  char dataFinal[max_payload_size];

  char sensorId[7] = "5ND1HU";

  char rawGasChar[8];
  dtostrf(rawGas, 6, 2, rawGasChar);
  char rawLightChar[8];
  dtostrf(rawLight, 6, 2, rawLightChar);
  char rawHumidityChar[8];
  dtostrf(rawHumidity, 6, 2, rawHumidityChar);
  char rawTemperatureChar[8];
  dtostrf(rawTemperature, 6, 2, rawTemperatureChar);
  sprintf(dataFinal,"%s:AQ=%s;HM=%s;TP=%s;LI=%s",sensorId,rawGasChar,rawHumidityChar,rawTemperatureChar,rawLightChar);

  Serial.println(dataFinal);

	  unsigned int payload_size = (unsigned)strlen(dataFinal);
    Serial.println(payload_size);
    // First, stop listening so we can talk.
    radio.stopListening();

    // Take the time, and send it.  This will block until complete
    Serial.print(F("Now sending length "));
    radio.write(dataFinal, payload_size );

    // Now, continue listening
    radio.startListening();

    // Wait here until we get a response, or timeout
    unsigned long started_waiting_at = millis();
    bool timeout = false;
    while ( ! radio.available() && ! timeout )
      if (millis() - started_waiting_at > 500 )
        timeout = true;

    // Describe the results
    if ( timeout )
    {
      Serial.println(F("Failed, response timed out."));
    }
    else
    {
      // Grab the response, compare, and send to debugging spew
      uint8_t len = radio.getDynamicPayloadSize();
      
      // If a corrupt dynamic payload is received, it will be flushed
      if(!len){
        return; 
      }
      
      radio.read( receive_payload, len );

      // Put a zero at the end for easy printing
      receive_payload[len] = 0;

      // Spew it
      Serial.print(F("Got response size="));
      Serial.print(len);
      Serial.print(F(" value="));
      Serial.println(receive_payload);
    }

    // Try again 1s later
    delay(10000);
  

}
