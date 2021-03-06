# GeckoBot
This repository provides the software for <a href="https://github.com/larslevity/ControlBoard">this Controlboard</a> or a similar device. 
Pneumatically operated soft robots can be controlled with the ControlBoard.
The code to be found here is specially tailored to the gecko-inspired soft robot - codenamed Geckobot as seen in the image below.
CAD data to build the robot can be found 
<a href="https://github.com/larslevity/CADGeckoBot">here</a>.
But in principle, all similar robots can also be operated with it.

![Image of the gecko inspired soft robot](https://github.com/larslevity/GeckoBot/blob/master/Pictures/robot_cboard.JPG)

## Walking Performance of the robot
The following motion picture shows the walking performance of the robot when running straight.
The whole video can be found <a href="https://github.com/larslevity/GeckoBotVideos">here</a>.

![Robot walking straight](https://github.com/larslevity/GeckoBot/blob/master/Pictures/smallbot.gif)

Using video analysis, the track of the robots feet can be obtained.
With the kinematic model (stated below) the best fitting pose is calculated for each frame of one walking cycle.
The motion picture below shows the result.

![The Track of feet during a straight walking cycle](https://github.com/larslevity/GeckoBot/blob/master/Pictures/track_of_feet.gif)


## Kinematic Model of the Robot

A kinematic model of the robot that is capable of predicting how the robot will deform under a given pressure can be found <a href="https://github.com/larslevity/GeckoBotModel">here</a>.
With the help of this model, new gait patterns can be tested much more easily.
The following figure shows the output of the model for the gait pattern of a curve.


![Output of kinematic model, when walking a circle](https://github.com/larslevity/GeckoBot/blob/master/Pictures/circle.gif)


## Structure of the Hardware and Code

The Picture below shows the Soft- and Hardware Architecture of the GeckoBot System.

![principle sketch of the hardware and software structure](https://github.com/larslevity/GeckoBot/blob/master/Pictures/gesamtsystem_HUI.png)


