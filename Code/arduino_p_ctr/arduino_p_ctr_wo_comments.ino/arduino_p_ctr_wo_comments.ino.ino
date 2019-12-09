

#include <Wire.h>

#define pressureSensor 0x28  //Pressure Sensor Address
#define PWM_PIN_IN A3           //Receiving Pin for BBB PWM Signal
#define PWM_PIN_OUT 6          //PWM output pin for proportional flow valve


// PSens
float output_pressure_sensor, output_min = 1638, output_max = 14745;
float pressure_max = 10.3421, pressure_min = 0; 
byte byte_one, byte_two; double currentPressure; 
// Reference 
int pwm_value; 
float DC; 
double referencePressure;

// PID
const double Kp=.6, Ki=.05, Kd=0.01;
// const double Kp=.6, Ki=.7, Kd=0.005;
const double max_output=.99, gam=.1, tsampling=10; 
double integral=0, last_err=0, last_out=0, windup_guard=0; 
double err, diff, integ, controller_output, u, u_ctr;


double sign(double val){
   double signum=0;
   if(val < 0){
     signum=-1;
   }
   else if(val>0){
     signum=1;
   }
   return signum;
}

double ctr_out(double reference, double system_output){
   err = reference - system_output;
   diff = (gam*Kd - tsampling/2)/(gam*Kd+tsampling/2)*last_out + Kd/(gam+tsampling/2)*(err-last_err);
   last_err = err;

   double integ = integral + tsampling*Ki*(err-windup_guard);
   if (abs(integ) > max_output){
     integ = max_output*sign(integ);
     }
   integral = integ;

   controller_output = Kp*(err+integ+diff);
   if (abs(controller_output)>max_output){
     windup_guard = controller_output*(1-max_output/abs(controller_output));
     last_out = max_output*sign(controller_output);
   }
   else {
     windup_guard = 0;
     last_out = controller_output;
   }
   return last_out;
}


double mapping(double x){
   double mapping=122.+(67.*x);
   return mapping;
}





void setup() {
   pinMode(PWM_PIN_IN, INPUT);     //Open Pin for PWM signal
   pinMode(PWM_PIN_OUT, OUTPUT);
   Serial.begin(9600);
   Wire.begin();                //Enable I2C Bus
   Wire.setClock(400000);       //Set I2C to fast mode
   Wire.beginTransmission(pressureSensor); //Begin transmission to pressure sensor
   Wire.endTransmission();                 // End Transmission
}


void loop() {
   // Read Reference
   pwm_value = analogRead(PWM_PIN_IN);    //read PWM Value on PWM_Pin
   DC = round((100./683.)*pwm_value);
   referencePressure= 1.*(DC/100);

   // Read PSens
   Wire.beginTransmission(pressureSensor); //Begin Transmission to Pressure Sensor
   Wire.requestFrom(pressureSensor, 2);   //Request two bytes from Pressure Sensor for Pressure reading
   byte_one=Wire.read();                     // Save first read Byte
   byte_two=Wire.read();                     // Save second read Byte
   output_pressure_sensor=byte_one*256+byte_two;             //calculate output using byte_one and two

    //Transfer function to get pressure in [Bar] from calculated output
   currentPressure=(((output_pressure_sensor-output_min)*(pressure_max-pressure_min))/(output_max-output_min))+pressure_min; 

   u_ctr = ctr_out(referencePressure, currentPressure);
   u = mapping(u_ctr);
   analogWrite(PWM_PIN_OUT, u);
   delay(tsampling-4);                   // -4 : give calculations some time ...

   //Serial.print("r=");
   //Serial.print(referencePressure);
   //Serial.print("\tp=");
   //Serial.print("\t");
   //Serial.print(currentPressure);
   //Serial.print("\tu_ctr=");
   //Serial.print("\t");
   //Serial.print(u_ctr);
   //Serial.print("\tu_map=");
   //Serial.print("\t");
   //Serial.print(u);
   //Serial.print("\tuV=");
   //Serial.print("\t");
   //Serial.println((u*10)/255);
}
