#!/usr/bin/env python

import roslib; roslib.load_manifest('fishgantry_ros')
import rospy
# from tetherfish_ros.msg import TetherFishMsg
import tf
import serial
import sys
import datetime
import rospkg
import nav_msgs
from geometry_msgs.msg import PoseStamped
import std_srvs.srv

class FishGantry():
  def __init__(self):
    self.port = rospy.get_param('~port','/dev/ttyACM0')
    self.baud = rospy.get_param('~baud',115200)
    self.ser = serial.Serial(self.port, self.baud,timeout=1) #this initializes the serial object
    self.pub= rospy.Publisher("fishgantry/robotpose",PoseStamped)
    self.goalpose_sub = rospy.Subscriber("/fishgantry/commandpose",PoseStamped,self.commandCallback)
    self.tailpose_sub = rospy.Subscriber("/fishgantry/tailpose",PoseStamped,self.tailCallback)
    #initialize a command position
    self.command = PoseStamped()
    self.command.header.stamp = rospy.Time.now()
    self.command.pose.position.x = 0
    self.command.pose.position.y = 0
    self.command.pose.position.z = 0
    self.command.pose.orientation.z = 0
    self.command.pose.orientation.x = 0
    self.tailcommand = 0;
    self.rollcommand,self.pitchcommand,self.yawcommand=0,0,0

    self.br = tf.TransformBroadcaster()

    rospy.Service('enable_motors',std_srvs.srv.Trigger,self.enable_motors)
    rospy.Service('disable_motors',std_srvs.srv.Trigger,self.disable_motors)
    rospy.Service('home_axes',std_srvs.srv.Trigger,self.home)


    #main loop runs on a timer, which ensures that we get timely updates from the gantry arduino
    rospy.Timer(rospy.Duration(.01),self.loop,oneshot=False) #timer callback (math) allows filter to run at constant time
    #subscribers (inputs)
    #construct the file name for our text output file
    rospack = rospkg.RosPack()
    # get the file path for rospy_tutorials
    self.package_path=rospack.get_path('fishgantry_ros')

  def tailCallback(self,data):
    self.tailcommand = data.pose.orientation.z
  def commandCallback(self,data):
    self.command.header.stamp = data.header.stamp
    self.command.pose.position.x = data.pose.position.x
    self.command.pose.position.y = data.pose.position.y
    self.command.pose.position.z = data.pose.position.z
    self.command.pose.orientation.z = data.pose.orientation.z
    self.command.pose.orientation.x = data.pose.orientation.x

    self.rollcommand,self.pitchcommand,self.yawcommand = tf.transformations.euler_from_quaternion(self.command.orientation)

    #print "received: "+str(self.command.pose.position.x)

  def enable_motors(self,event):
    encommand = -333.30
    serstring = '!'+"{0:.3f}".format(encommand)+','+"{0:.3f}".format(encommand)+','+"{0:.3f}".format(encommand)+','+"{0:.3f}".format(encommand)+','+"{0:.3f}".format(encommand)+','+"{0:.3f}".format(0)+'\r\n'
    print "sending: "+serstring
    self.ser.write(serstring)
    line = self.ser.readline()
    print line

  def disable_motors(self,event):
    discommand = -333.30
    serstring = '!'+"{0:.3f}".format(discommand)+','+"{0:.3f}".format(discommand)+','+"{0:.3f}".format(discommand)+','+"{0:.3f}".format(discommand)+','+"{0:.3f}".format(discommand)+','+"{0:.3f}".format(0)+'\r\n'
    print "sending: "+serstring
    self.ser.write(serstring)
    line = self.ser.readline()
    print line
  def home(self,event):
    homecommand = -333.30
    serstring = '!'+"{0:.3f}".format(homecommand)+','+"{0:.3f}".format(homecommand)+','+"{0:.3f}".format(homecommand)+','+"{0:.3f}".format(homecommand)+','+"{0:.3f}".format(homecommand)+','+"{0:.3f}".format(0)+'\r\n'
    print "sending: "+serstring
    self.ser.write(serstring)
    line = self.ser.readline()
    print line

  def loop(self,event):
    serstring = '!'+"{0:.3f}".format(self.command.pose.position.x)+','+"{0:.3f}".format(-self.command.pose.position.y)+','+"{0:.3f}".format(self.command.pose.position.z)+','+"{0:.3f}".format(self.pitchcommand)+','+"{0:.3f}".format(self.yawcommand)+','+"{0:.3f}".format(self.tailcommand)+'\r\n'
    # print "sending: "+serstring
    self.ser.write(serstring)
    line = self.ser.readline()
    # print line
    linestrip = line.strip('\r\n')
    linesplit = line.split()
    if len(linesplit)>=3:
      #print shotslast, arduinonumshots,shotslast==(arduinonumshots+1)
      
      try:
        msg = PoseStamped()
        msg.header.stamp = rospy.Time.now()
        msg.pose.position.x = float(linesplit[0])
        msg.pose.position.y = float(linesplit[1])
        msg.pose.position.z = float(linesplit[2])
        pitchback = float(linesplit[3])
        yawback = float(linesplit[4])

        quat = tf.transformations.quaternion_from_euler(0,pitchback,yawback)

        #msg.arduino_time = float(linesplit[2])
        #msg.tailfreq= float(linesplit[3])
        #msg.tailamp = float(linesplit[4])
        #msg.tailangle = float(linesplit[5])
        #print "publishing"
        self.pub.publish(msg)
              
      except:
        print "OOPS! BAD LINE"
        #ef.write("problem  with serial line"+"\r\n")

      
#main function
def main(args):
  rospy.init_node('gantry_node', anonymous=True)
  encreader = FishGantry()
  
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print "Shutting down"

if __name__ == '__main__':
    main(sys.argv) 