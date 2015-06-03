from __future__ import division # for proper float division

import os
import sys
from ddapp import botpy
import math
import time
import types
import functools
import random
import numpy as np
from ddapp import ik
from ddapp import ikconstraints
from ddapp import ikconstraintencoder
import drc as lcmdrc
import json
from ddapp.utime import getUtime
from ddapp import lcmUtils


class PlannerPublisher(object):

  def __init__(self, ikPlanner, affordanceMan):
    self.ikPlanner = ikPlanner
    self.affordanceManager = affordanceMan

  def processIK(self, constraints):
    listener = self.ikPlanner.getManipIKListener()
    self.ikPlanner.ikConstraintEncoder.publishConstraints( constraints, messageName='IK_REQUEST')
    ikplan = listener.waitForResponse(timeout=12000)
    listener.finish()

    endPose = [0] * self.ikPlanner.jointController.numberOfJoints
    if ikplan.num_states>0:
      endPose[len(endPose)-len(ikplan.plan[ikplan.num_states-1].joint_position):] = ikplan.plan[ikplan.num_states-1].joint_position
      info=ikplan.plan_info[ikplan.num_states-1]
    else: 
      info = -1
    return endPose, info

  def processTraj(self, constraints, poseEnd, nominalPoseName):
    # Temporary fix / HACK / TODO (should be done in exotica_json)
    largestTspan = [0, 0]
    for constraintIndex, _ in enumerate(constraints):
      if isinstance(constraints[constraintIndex], ikconstraints.PostureConstraint):
        if constraints[constraintIndex].postureName == 'gaze_plan_start':
          #print "(gaze_plan_start) Temporary start pose rewrite hack activated"
          constraints[constraintIndex].__setattr__('postureName','reach_start')

      # Get tspan extend to normalise time-span
      if np.isfinite(constraints[constraintIndex].tspan[0]) and np.isfinite(constraints[constraintIndex].tspan[1]):
        largestTspan[0] = constraints[constraintIndex].tspan[0] if (constraints[constraintIndex].tspan[0] < largestTspan[0]) else largestTspan[0]
        largestTspan[1] = constraints[constraintIndex].tspan[1] if (constraints[constraintIndex].tspan[1] > largestTspan[1]) else largestTspan[1]

    # Temporary fix / HACK/ TODO to normalise time spans
    for constraintIndex, _ in enumerate(constraints):
      if np.isfinite(constraints[constraintIndex].tspan[0]) and np.isfinite(constraints[constraintIndex].tspan[1]):
        if largestTspan[1] != 0:
          constraints[constraintIndex].tspan[0] = constraints[constraintIndex].tspan[0] / largestTspan[1]
          constraints[constraintIndex].tspan[1] = constraints[constraintIndex].tspan[1] / largestTspan[1]

    self.publishCollisions()
    listener = self.ikPlanner.getManipPlanListener()
    constraintSet = ikplanner.ConstraintSet(self, constraints, poseEnd, nominalPoseName)
    self.ikPlanner.ikConstraintEncoder.publishConstraints( constraintSet.constraints, 'PLANNER_REQUEST')
    lastManipPlan = listener.waitForResponse(timeout=20000)
    listener.finish()
    return lastManipPlan, lastManipPlan.plan_info[0]

  def processAddPose(self, pose, poseName):
    # Temporary fix / HACK / TODO (should be done in exotica_json)
    if poseName == 'gaze_plan_start':
      #print "(gaze_plan_start) Temporary start pose rewrite hack activated"
      poseName = 'reach_start'
    elif poseName == 'q_start':
      #print "(q_start) Temporary start pose rewrite hack activated"
      poseName = 'reach_start'

    msg = lcmdrc.planner_request_t()
    msg.utime = getUtime()
    msg.poses = json.dumps({poseName:list(pose)})
    msg.constraints = ''
    lcmUtils.publish('PLANNER_SETUP_POSES', msg)

  def publishJointNames(self):
    msg1 = lcmdrc.robot_state_t()
    msg1.joint_name = list(self.ikPlanner.jointController.jointNames)
    msg1.num_joints = len(msg1.joint_name)
    msg1.joint_position = [0]*msg1.num_joints
    msg1.joint_velocity = [0]*msg1.num_joints
    msg1.joint_effort = [0]*msg1.num_joints
    lcmUtils.publish('PLANNER_SETUP_JOINT_NAMES', msg1) 

  def publishCollisions(self):
    affs = self.affordanceManager.getCollisionAffordances()
    msg = lcmdrc.affordance_collection_t()
    msg.utime = getUtime()
    s='['
    first=True
    for aff in affs:
      des=aff.getDescription()
      classname=des['classname'];
      if first:
        s+='{'
      else:
        s+='\n,{'
      first=False
      s+='"classname":"'+classname+'"'
      s+=',"uuid":"'+des['uuid']+'"'
      s+=',"pose": {"position":{"__ndarray__":'+repr(des['pose'][0].tolist())+'},"quaternion":{"__ndarray__":'+repr(des['pose'][1].tolist())+'}}'
      if classname=='MeshAffordanceItem':
        s+=',"filename":"'+aff.getMeshManager().getFilesystemFilename(des['Filename'])+'"'
      if classname=='SphereAffordanceItem':
        s+=',"radius":'+repr(des['Radius'])
      if classname=='CylinderAffordanceItem' or classname=='CapsuleAffordanceItem':
        s+=',"radius":'+repr(des['Radius'])
        s+=',"length":'+repr(des['Length'])
      if classname=='BoxAffordanceItem':
        s+=',"dimensions":'+repr(des['Dimensions'])
      if classname=='CapsuleRingAffordanceItem':
        s+=',"radius":'+repr(des['Radius'])
        s+=',"tube_radius":'+repr(des['Tube Radius'])
        s+=',"segments":'+repr(des['Segments'])
      s+='}'
    msg.name=s+']'
    lcmUtils.publish('PLANNER_SETUP_COLLISION_AFFORDANCES', msg)
import ikplanner