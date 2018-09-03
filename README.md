# GeckoBot
This repository provides the software for <a href="https://github.com/larslevity/ControlBoard">this Controlboard</a> or a similar device. 
Pneumatically operated soft robots can be controlled with the ControlBoard.
The code to be found here is specially tailored to the gecko-inspired soft robot - codenamed Geckobot as seen in the image below.
But in principle, all similar robots can also be operated with it

![Image of the gecko inspired soft robot](https://github.com/larslevity/GeckoBot/blob/master/Pictures/robot_cboard.JPG)




## Structure of the Hardware and Code

![principle sketch of the hardware and software structure](https://github.com/larslevity/GeckoBot/blob/master/Pictures/gesamtsystem_HUI.png)

## Kinematic Model of the Robot

This also provides a kinematic model of the robot that is capable of predicting how the robot will deform under a given pressure.
With the help of this model, new gait patterns can be tested much more easily.
The following figure shows the output of the model for the gait pattern of a curve.

![Output of kinematic model, when walking a circle](https://github.com/larslevity/GeckoBot/blob/master/Pictures/model.png)

![Output of kinematic model, when walking a circle](https://github.com/larslevity/GeckoBot/blob/master/model/circle.gif)
