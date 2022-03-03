# **Folder _Obsolete**
The obsolete folder contains all machine learning performed on the `MyFitnessPAL` dataset. These tests, as noted, where performed with the intent to find the best possible model for our application. You may replicate these experiments, or even better, when you make your alterations and incorporate your ideas, you may use it to figure out the best candidate.
* `python _obs_create_models.py`
    * Creates DataFrames on every possible `Days/Weeks`, `Keep/Jump`, `TIC`, `LogT` combination.
    * You need to manually select whether you want `Deficit` or `Lapse` prediction.
        * Once during the Day(s) to Day scenario and once during the Week(s) to Week scenario.
    * After creating the DataFrames, it will create models like the ones described above and train them.
        * No need for assigning parameters. Optimal settings have been selected.
    * Upon completion of fitting, the following will occur:
        * `Evaluation` on both cases (`Deficit/Lapse`)
        * Saving of `History` and `Metrics` dictionaries on both cases.
        * In the case of `Lapse`, we make **1000** predictions to roughly figure out a baseline accuracy and its difference with our model.
            * We avoid using the entire testing set because it will take too long even for one model, let alone 154/28.
            * These will be printed on screen
            * The `Accuracy` dictionary will be saved as well.

## What to do with those models
* `python _obsolete/ml/create_frame_plots.py`
    * Creates certain plots depending on circumstances. Easily navigatable. You may choose between:
        * `[Days, Weeks]` depending on your preference. 
            * Accepts empty argument, defaults to `days`
        * `[all, 1-7]` preference on LogT variable.
            * All option will create all plots together one on top of the other. Ideal to compare results.
            * Accepts empty argument, defaults to `'all'`
        * `[0, 1]` deficit/lapse prediction.
            * Accepts empty argument, defaults to `0`

## **Additional, Preliminary Tests**
* `python _obsolete/ml/_regression/regression.py`
    * A simple regression test where we try to predict calorie deficits through nutrient deficits. Our goal here is to re-affirm that nutrients can reliably estimate the amount of calories. Since we will be making predictions later on, it makes sense to at least know that what we are using is potent. 
    * No parameters, simply run!

* `python _obsolete/ml/_classification/classification.py`
    * A simple 7-way classification where we try to group days into certain classes. Our goal again is to prove that it is possible to use nutrients to estimate how bad or how good days can be.
    * No parameters, simply run!