Overall:
--------
Contains everything used concerning Machine Learning in the Website Application. 
* Data contains all saved models, variables/dictionaries (pickle) to be used during the application.
* Preprocessing contains python scripts used during the creation of the datasets.
* z_d2d and z_w2w are the main folders that contain the creation and training of the two models (to be used in the website).
 * The data_preparation.py in both instances calls from preprocessing.

Parameter Explanation:
----------------------
When running scripts, certain inputs might be required. These consist of:
1. Days/Weeks taken into consideration
    * You may choose as you wish, although values in the mid range are probably the best combination of good results and reliability.
    * Days from 1 to 11, Weeks from 1 to 4
2. LogT
    * This parameter purges the dataset from raws containing less logs than its value. Its value ranges from 1 to 7.
    * You may again choose as you wish but likewise, values in the mid range are probably the best combination of good results and reliability.
3. Append Site Data
    * You may append site data into the mix, essentially giving the system some info on the site users who logged at least some days
    * Theoretically if we had a big dataset from the website we would only be using this.
    * Choose as you wish, although since the site logs are generally more than the dataset logs this will have a minor penalty in the results.
4. Choosing between Training-Only, Training & Validation, Training & Validation & Testing.
    * Implemented following the logic of training up to time T and then predicting from time T onwards.
    * Normally because we'd rather include everything.
5. Choosing between Tensorboard or not.
    * If desired, you may keep tensorboard logs and then run tensorboard --logdir logs (or logsw) to access them on your browser.
    * Normally we are not interested for tensorboard.
6. Choosing between Deficit and Lapse prediction.
    * Deficit Prediction (Regression) predicts the deficit % in calories of the next day/week.
    * Lapse prediction (Classification) predicts between two classes, which we differentiate by targeting the 50% baseline point (mean of the label).  

create_frame_plots.py:
----------------------
A script that prints certain plots based on the input given. For testing and ease-of-access reasons. Not as eloquent as the one in _obsolete/ml  
**ToRun**: Simply execute the file.

ml_preparation.py:
------------------
A script containing functions designed to be imported by the two main variations.