#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <ESP8266HTTPClient.h>
#include <Arduino_JSON.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <Servo.h>

//timer
unsigned long timer_delay_request = (30 * 60000); //30 min
unsigned long last_time_request = 0;

unsigned long timer_delay_pump = (10 * 1000); //10 sec
unsigned long last_time_pump = 0;
bool pump_working = false;

unsigned long timer_delay_barrier = (3 * 1000); //3 sec
unsigned long last_time_barrier = 0;
bool barrier_open = true;

//WiFi Credentials (2.4ghz)
const char *ssid = "WIFI_SSID";
const char *password = "WIFI_PASSWORD";

//AWS APIGW Connection
const char *API_KEY = "AWS_APIGW_APIKEY";

//rfid
#define RST_PIN D3
#define SS_PIN D4
MFRC522 rfid(SS_PIN, RST_PIN);
long card_uid = 0;

//servo
int servo_pin = 5;
Servo myservo;

//machine leds and button
int machine1_led_pin = 16;
int machine2_led_pin = 1;
int machine2_button_pin = 4;
int machine2_working = 1;

//dht
#define DHTPIN 10
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
float humedity = 0;
float temperature = 0;

//water pump
const int relay_pin = 15;
unsigned long pump_on_timer = 0;
float water_tank_level = 0;

void wifi_connect(){
  WiFi.mode(WIFI_OFF);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("\nConnecting");
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.print("\nConnected to ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}//fin wifi_connect

void post_request_apigw(String path){

  JSONVar payload_json;
  payload_json["temperatura"] = temperature;
  payload_json["humedad"] = humedity;
  payload_json["nivel_tanque_agua"] = water_tank_level;
  payload_json["identificador_tarjeta"] = card_uid;
  payload_json["encendido_bomba_segundos"] = pump_on_timer;
  payload_json["maquina1"] = 1;
  payload_json["maquina2"] = machine2_working;
  String payload = JSON.stringify(payload_json);

  WiFiClientSecure client;
  HTTPClient http;
  client.setInsecure();
  client.setTimeout(30000);

  String url = "https://hna219z24l.execute-api.us-east-1.amazonaws.com" + path;
 
  Serial.println("Secure POST Request to " + String(url));
  Serial.println("Payload: " + payload);
 
  http.begin(client, url);
  http.addHeader("x-api-key", API_KEY);
  http.addHeader("Content-Type", "application/json");
 
  int httpResponseCode = http.POST(payload);

  String response = "Response: " + http.getString();

  Serial.print("HTTP Response code: " + httpResponseCode);
  Serial.println(response);
 
  http.end();
  Serial.println("closing connection");
  Serial.println();

  card_uid = 0;
  pump_on_timer = 0;
  last_time_request = millis();
   
}// fin post_request_apigw

void start_rfid(){
  //RFID
  SPI.begin();      // Init SPI bus
  rfid.PCD_Init();   // Init MFRC522
}

void test_rfid_connection() {
  bool result = rfid.PCD_PerformSelfTest();
  Serial.print(F("\nPrueba de conexion con RFID: "));
  if (result)
    Serial.println(F("Conectado"));
  else
    Serial.println(F("Desconectado"));
}

void open_barrier(){
  Serial.println("Abriendo barrera");
  myservo.write(70);
  last_time_barrier = millis();
  barrier_open = true;
}

void close_barrier(){
  if (barrier_open) {
    if (millis() - last_time_barrier > timer_delay_barrier){
      Serial.println("Cerrando barrera");
      myservo.write(150);
      barrier_open = false;
    }
  }
}

long get_rfid_uid() {
  if ( ! rfid.PICC_ReadCardSerial()) { //stop once get serial card
    return -1;
  }
  unsigned long hex_num;
  hex_num =  rfid.uid.uidByte[0] << 24;
  hex_num += rfid.uid.uidByte[1] << 16;
  hex_num += rfid.uid.uidByte[2] <<  8;
  hex_num += rfid.uid.uidByte[3];
  rfid.PICC_HaltA(); // stop reading
  return hex_num;
}

void check_in(){
  if (rfid.PICC_IsNewCardPresent()) {
    unsigned long uid = get_rfid_uid();
    if (uid != -1) {
      Serial.println("Tarjeta detectada, UID: " + String(uid));
      card_uid = uid;
      open_barrier();
      post_request_apigw("/dev/data/upload");
    }
  }
}

void water_pump(float water_tank_level){
  if (pump_working) {
    if (millis() - last_time_pump > timer_delay_pump){
      digitalWrite(relay_pin, LOW);
      pump_working = false;
      pump_on_timer = pump_on_timer + 10;
      last_time_pump = millis();
    }
  } else if (water_tank_level <= 200){
    Serial.println("bomb pupm set on for 10 secs");
    digitalWrite(relay_pin, HIGH);
    pump_working = true;
    last_time_pump = millis();
  }
}

void check_machine(){
  if (digitalRead(machine2_button_pin) == HIGH) {
    if (machine2_working){
      digitalWrite(machine2_led_pin, LOW);
      machine2_working = 0;
    } else {
      digitalWrite(machine2_led_pin, HIGH);
      machine2_working = 1;
    }
  }
}

void reset(){
  close_barrier();
}

void read_all_sensors(){
  Serial.println("Reading sensors...");

  temperature = read_temperature();
  humedity = read_humedity();
  water_tank_level = read_water_tank();

  Serial.println("Humedad: " + String(humedity));
  Serial.println("Temperatura: " + String(temperature));
  Serial.println("Nivel de agua en tanque: " + String(water_tank_level));
}

void start_dht(){
  dht.begin();
}

float read_temperature(){
  return dht.readTemperature();
}

float read_humedity(){
  return dht.readHumidity();
}

float read_water_tank(){
  return analogRead(A0);
}

void setup() {
  delay(1000);
  Serial.begin(115200);
  delay(1000);
  while (!Serial){}
  wifi_connect();
  start_rfid();
  start_dht();
  myservo.attach(servo_pin);
  close_barrier();
  pinMode(relay_pin, OUTPUT);
  digitalWrite(relay_pin, LOW);
  
  pinMode(machine1_led_pin, OUTPUT);
  digitalWrite(machine1_led_pin, LOW);
  pinMode(machine2_led_pin, OUTPUT);
  digitalWrite(machine2_led_pin, LOW);
  pinMode(machine2_button_pin, INPUT);
}// fin setup

void loop() {
  delay(100);
  test_rfid_connection();
  check_in();
  check_machine();
  read_all_sensors();
  water_pump(water_tank_level);
  
  Serial.println("Current time " + String(millis()) + " ms");
  Serial.println("Last time " + String(last_time_request) + " ms");
  Serial.println("Delay time " + String(timer_delay_request) + " ms");
  Serial.println("Pump on timer " + String(pump_on_timer) + " s");

  if (millis() - last_time_request > timer_delay_request){
    post_request_apigw("/dev/data/upload");
  }

  delay(100);
  reset();

}//fin loop
