# Transmission Parameters

These parameters control the characteristics of the how the viral is transmitted. 
In the superspreader model this is controlled by four different parameters.

## Population Spread (R0):

This is the standard R0 value which the SEIR model deals with, it represents the number of people 
infected on average by a sick person. In real world terms these would be infections spread at parks, grocery stores or other day to day interactions.

## Population->Spreader Spread:

How many superspreader groups are infected by the average infected person. In real world terms these would be infections where a sick person entered a nursing home, prison or some other high risk environment.

Note: In the Web UI this is denominated in infections per 1000.

## Spreader -> Population Spread:

How many people are infected by the average superspreader group. In real world terms these would be infections caused when infected people from a high risk population expose members of the general population. For instance if members of a meat packing plant come home and expose their families.

Note: This value is based on the full superspreader group's infection. If the R0 for an individual member of the group is .2 then for a 500 person group the group R0 would be 100.

## Spreader -> Spreader Spread:

How many other superspreader groups are infected by the average superspreader group. In real world terms these would be infections caused when infected people from different high risk environments are exposed to each other. For example a hospital with many different nursing home residents could be a vector for this type of transmission.

Note: This value is based on the full superspreader group's infection. If only one percent of infections infect somebody in a different high risk group then with a group size of 500 the R0 value would be 5.

# Population Parameters:

These parameters control characteristics of the location being infected.

## Population Size:

Self explanatory, the number of people in the modelled population.

## Initial Infections:

The number of people in the general population who are infected at t=0. At the start of the simulation no superspreader groups are infected.

## Number Spreader Groups:

The number of superspreader groups in the population. Note that the model does not take into account the size of these groups and only infections among the general population are considered.

# Graph Parameters:

These parameters control aspects of how the results of the simulation are displayed.

## YMax:

Controls the upper bound of the YAxis. If set to 0 (the default) then the upper bound will be computed dynamically based on the data.

