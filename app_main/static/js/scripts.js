$("form[name=signup_form").submit(function(e) {
    /**
     * Signup Form Function
     * takes the form arguments, creates the user and moves him to the dashboard.
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    $.ajax({
        url: "/user/signup",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            window.location.href = "/dashboard/";
        },
        error: function(resp) {
            console.log(resp);
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });

    e.preventDefault(); 
});

$("form[name=login_form").submit(function(e) {
    /**
     * Login Form Function
     * takes the form arguments, logins the user (if correct) and moves him to the dashboard.
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    $.ajax({
        url: "/user/login",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            window.location.href = "/dashboard/";
        },
        error: function(resp) {
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });

    e.preventDefault(); 
});

$("form[name=day_input_form").submit(function(e) {
    /**
     * Obsolete Submit Day Form
     * used to be a form that would log a day of inputs all-together. REMOVED
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    $.ajax({
        url: "/user/submit_day",
        type: "POST",
        data: data,
        dataType: "json",
        success: function(resp) {
            window.location.href = "/dietbook/";
        },
        error: function(resp) {
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });

    e.preventDefault(); 
});

$(document).ready(function(){
    /**
     * DietBook function
     * defines Dietbook parameters and makes the table editable.
     */
    var dataTable = $('#user_dietbook').DataTable( {
        "lengthMenu": [ 7 ],
        "bSort": false, 
        "paging": false,
        "searching": false,
        "bInfo" : false
    });
    $.fn.editable.defaults.mode = 'inline';
    $('#user_dietbook').editable({
        container:'body',
        selector:'td.breakfast',
        url:'/updatebook',
        title:'breakfast',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        },
        success: function(response) {
            $('#user_dietbook').html(response);
        }
    });
 
    $('#user_dietbook').editable({
        
        container:'body',
        selector:'td.brunch',
        url:'/updatebook',
        title:'brunch',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        },
        success: function(response) {
            $('#user_dietbook').html(response);
        }
    });
 
    $('#user_dietbook').editable({
        container:'body',
        selector:'td.lunch',
        url:'/updatebook',
        title:'lunch',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        },
        success: function(response) {
            $('#user_dietbook').html(response);
        }
    });

    $('#user_dietbook').editable({
        container:'body',
        selector:'td.snack',
        url:'/updatebook',
        title:'snack',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        },
        success: function(response) {
            $('#user_dietbook').html(response);
        }
    });

    $('#user_dietbook').editable({
        container:'body',
        selector:'td.dinner',
        url:'/updatebook',
        title:'dinner',
        type:'POST',
        validate:function(value){
            if($.trim(value) == '')
            {
                return 'This field is required';
            }
        },
        success: function(response) {
            $('#user_dietbook').html(response);
        }
    });

    $(document).ready(function() {
        /**
         * Previous Button Function
         * Moves Week-View back one week.
         */
        $(document).on('click', '.prev', function() {
    
            var current = $(this).attr('prev');
            var col = $(this).attr('col');
            var day_int = parseInt(current, 10);
            var dt = new Date(day_int);
            dt.last().monday();
            timestamp = dt.getTime();
            timestamp = timestamp / 1000;
            type_of_request = 0;
    
            req = $.ajax({
                url : '/updateweek',
                type : 'POST',
                data : { timestamp: timestamp, col: col, type_of_request: type_of_request }
            });
    
            req.done(function(data) {
    
                $('#user_dietbook').fadeOut(0000).fadeIn(1000);
                //$('#memberNumber'+member_id).text(data.member_num);
                $('#user_dietbook').html(data);
    
            });
        
    
        });
    
    });
    
    $(document).ready(function() {
        /**
         * Next Button Function
         * Moves Week-View forward one week.
         */
        $(document).on('click', '.next', function() {
    
            var current = $(this).attr('next');
            var col = $(this).attr('col');
            var day_int = parseInt(current, 10);
            var dt = new Date(day_int);
            timestamp = dt.getTime();
            timestamp = timestamp / 1000;
            type_of_request = 0; 
    
            req = $.ajax({
                url : '/updateweek',
                type : 'POST',
                data : { timestamp: timestamp, col: col, type_of_request: type_of_request }
            });
    
            req.done(function(data) {
    
                $('#user_dietbook').fadeOut(0000).fadeIn(1000);
                //$('#memberNumber'+member_id).text(data.member_num);
                $('#user_dietbook').html(data);
    
            });
        
    
        });
    
    });

    $(document).ready(function() {
        /**
         * Predict Week Deficit Button
         * Makes deficit prediction on displayed Week
         */
        $(document).on('click', '.predict_week_deficit', function() {
    
            var date = $(this).attr('predict_week_deficit');
            var col = $(this).attr('col');
            type_of_request = 2; 
            //alert(date);
    
            req = $.ajax({
                url : '/predict_calorie_deficit',
                type : 'POST',
                data : { date: date, col: col, type_of_request: type_of_request }
            });
    
            req.done(function(data) {
    
                alert(data)
    
            });
        
        });
    
    });

    $(document).ready(function() {
        /**
         * Predict Deficit Button
         * Makes deficit prediction on selected day
         */
        $(document).on('click', '.predict_deficit', function() {
    
            var date = $(this).attr('predict_deficit');
            var col = $(this).attr('col');
            type_of_request = 1; 
            //alert(date);
    
            req = $.ajax({
                url : '/predict_calorie_deficit',
                type : 'POST',
                data : { date: date, col: col, type_of_request: type_of_request }
            });
    
            req.done(function(data) {
    
                alert(data)
    
            });
        
        });
    
    });

    $(document).ready(function() {
        /**
         * Expand Day Button
         * expands day
         */
        $(document).on('click', '.expand_day', function() {
    
            var date = $(this).attr('expand_day');
            var col = $(this).attr('col');
            type_of_request = 1; 
            // alert(current);
    
            req = $.ajax({
                url : '/updateweek',
                type : 'POST',
                data : { date: date, col: col, type_of_request: type_of_request }
            });
    
            req.done(function(data) {
    
                $('#user_dietbook').fadeOut(0000).fadeIn(1000);
                $('#user_dietbook').html(data);
    
            });
        
        });
    
    });

    $(document).ready(function() {
        /**
         * Expand Week Button
         * returns from Day-View to Week-View
         */
        $(document).on('click', '.expand_week', function() {
    
            var date = $(this).attr('expand_week');
            var col = $(this).attr('col')
            date = date.split(' ')[0];
            // alert(date);
    
            req = $.ajax({
                url: "/dietbook_specific_load",
                type: "POST",
                data: { date: date, col: col }
            });
        
            req.done(function(data) {
        
                $('#user_dietbook').fadeOut(0000).fadeIn(2000);
                $('#user_dietbook').html(data);
            });
        
    
        });
    
    });

    $(document).ready(function() {
        /**
         * Checkbox Exercise Option
         * enables/disables the exercise checkbox
         */
        $(document).on('click', '.checkbox_exercise', function() {
            var pk_text = $(this).attr('data');
            var value = $(this).attr('value');
            req = $.ajax({
                url: "/updatebook",
                type: "POST",
                data: { pk: pk_text, value: value }
            });
            req.done(function(data) {
        
                $('#user_dietbook').fadeOut(0000).fadeIn(0000);
                $('#user_dietbook').html(data);
            });
        });
    });

    $(document).ready(function() {
        /**
         * Exercise Burnout
         * sets the exercise burnout 
         */
        $(document).on('keypress', '.exercise_burnout', function(event) {
            if (event.keyCode === 13) {
                var pk_text = $(this).attr('data');
                var value = $(this).find("input").val()
                req = $.ajax({
                    url: "/updatebook",
                    type: "POST",
                    data: { pk: pk_text, value: value }
                });
                req.done(function(data) {
            
                    $('#user_dietbook').fadeOut(0000).fadeIn(0000);
                    $('#user_dietbook').html(data);
                });
            }
        });
    });

    $(document).ready(function() {
        /**
         * Misc Select
         * checks/unchecks the miscellaneous options.
         */
        $(document).on('change', '.misc_select', function() {
            var pk_text = $(this).attr('data');
            var value = $(this).find("select").val()
            req = $.ajax({
                url: "/updatebook",
                type: "POST",
                data: { pk: pk_text, value: value }
            });
            req.done(function(data) {
        
                $('#user_dietbook').fadeOut(0000).fadeIn(0000);
                $('#user_dietbook').html(data);
            });
        });
    });

    $(document).ready(function() {
        /**
         * Weight Measurmenent
         * sets the weight measurement option (last in list)
         */
        $(document).on('keypress', '.weight_measurement', function(event) {
            if (event.keyCode === 13) {
                var pk_text = $(this).attr('data');
                var value = $(this).find("input").val()
                req = $.ajax({
                    url: "/updatebook",
                    type: "POST",
                    data: { pk: pk_text, value: value }
                });
                req.done(function(data) {
            
                    $('#user_dietbook').fadeOut(0000).fadeIn(0000);
                    $('#user_dietbook').html(data);
                });
            }
        });
    });

}); 
function del(ID){
    /**
     * Delete Day Function
     * old function that would remove day. REMOVED because it caused inconsistencies with MongoDB.
     */
    if (confirm("Are you sure you want to delete this day?")){
        window.location.href = '/delete/' + ID;
    }
}

// Below we are catching the user's dietbook

$("form[name=userbook_catch").submit(function(e) {
    /**
     * User dietbook catch
     * we are 'catching' the user's dietbook and appear it on the screen
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    req = $.ajax({
        url: "/dietbook_uselect",
        type: "POST",
        data: data
    });

    req.done(function(data) {

        $('#user_dietbook').fadeOut(0000).fadeIn(2000);
        $('#user_dietbook').html(data);
    });

    e.preventDefault(); 
});


$("form[name=prof_assistance").submit(function(e) {
    /**
     * Add Supervisor
     * we are adding ourselves to a prof. supervisor's list of patients.
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    $.ajax({
        url: "/addprof",
        type: "POST",
        data: data,
        success: function(resp) {
            window.location.href = "/dashboard/";
        },
        error: function(resp) {
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });

    e.preventDefault(); 
});

$("form[name=date_catch").submit(function(e) {
    /**
     * Date Catch
     *  we are catching the specific date chosen by the user in DietBook
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize().substr(9);

    req = $.ajax({
        url: "/dietbook_specific_load",
        type: "POST",
        data: { date_get: data, col: "default" }
    });

    req.done(function(data) {

        $('#user_dietbook').fadeOut(0000).fadeIn(2000);
        $('#user_dietbook').html(data);
    });

    e.preventDefault(); 
});

function loadToday() {
    /**
     * Load Today
     *  automatically loads today as a starting date to DietBook (when we enter the Interactive Dietbook)
     */
    req = $.ajax({
        url: "/dietbook_automatic_load",
        type: "POST"
    });

    req.done(function(data) {

        $('#user_dietbook').fadeOut(0000).fadeIn(3500);
        $('#user_dietbook').html(data);
    });

    e.preventDefault();
}

$("form[name=edamam_query").submit(function(e) {
    /**
     * Simple Query to Edamam function
     *  implements the Edamam Implementation card on the dashboard.
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();

    $.ajax({
        url: "/edamam_rquery",
        type: "POST",
        data: data,
        success: function(resp) {
            window.location.href = "/dashboard/";
        },
        error: function(resp) {
            $error.text(resp.responseJSON.error).removeClass("error--hidden")
        }
    });

    e.preventDefault(); 
});

$("form[name=personal_information").submit(function(e) {
    /**
     * Submiting personal information
     *  this function handles the personal information card on the dashboard
     */
    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    // alert(data);

    req = $.ajax({
        url: "/update_info",
        type: "POST",
        data: data
    });

    req.done(function(data) {

        $('#personal_information').fadeOut(0000).fadeIn(2000);
        $('#personal_information').html(data);
    });

    e.preventDefault(); 
});