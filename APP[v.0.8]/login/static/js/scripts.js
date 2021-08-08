$("form[name=signup_form").submit(function(e) {

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
    if (confirm("Are you sure you want to delete this day?")){
        window.location.href = '/delete/' + ID;
    }
}

// Below we are catching the user's dietbook

$("form[name=userbook_catch").submit(function(e) {

    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize();
    // alert(data);

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

// Below we are adding a prof. assistance for the user

$("form[name=prof_assistance").submit(function(e) {

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

// Below we are catching the specific date chosen by the user in DietBook

$("form[name=date_catch").submit(function(e) {

    var $form = $(this);
    var $error = $form.find(".error");
    var data = $form.serialize().substr(9);
    // alert(data);

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

// This fuction automatically loads today as a starting date to DietBook

function loadToday() {

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

// This faction does a query to Edamam

$("form[name=edamam_query").submit(function(e) {

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

// Submiting our personal info

$("form[name=personal_information").submit(function(e) {

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