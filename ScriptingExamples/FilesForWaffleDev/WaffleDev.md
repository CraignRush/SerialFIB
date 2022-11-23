## Waffle, Waffle, Waffle


# How to?

1. Copy the pattern files Notch.pf and Trenches.pf and the lamella protocol lamellamill.pro from SerialFIB/ScriptingExamples/FilesforWaffleDev to your own output directory
2. Set the output directory
2. Adjust the pattern files and protocol to your needs

   3. Caveat: If you modify the pattern files, please be aware that the alignment might not work anymore. To circumvent this, you will have to create alignment images containing the exact pattern structures. 

3. Load the alignment images for the milling of the notch and lamella in this order. These will be cross-correlated with after your trench milling to ensure the correct positioning.
4. Setup of the lamellae:

   1. Acquire an IB image and add the trench positions at perpendicular to the sample
   2. Acquire an IB image and add the position of the notch and lamella from the tilted grid
   3. It is strictly necessary to add the positions **always** consecutively one after another (1: Trench1, 2:Lamella&Notch1, 3:Trench2...)
5. 