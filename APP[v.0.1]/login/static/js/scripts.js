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
    
            req = $.ajax({
                url : '/updateweek',
                type : 'POST',
                data : { timestamp: timestamp, col: col }
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
    
            req = $.ajax({
                url : '/updateweek',
                type : 'POST',
                data : { timestamp: timestamp, col: col }
            });
    
            req.done(function(data) {
    
                $('#user_dietbook').fadeOut(0000).fadeIn(1000);
                //$('#memberNumber'+member_id).text(data.member_num);
                $('#user_dietbook').html(data);
    
            });
        
    
        });
    
    });
}); 
function del(ID){
    if (confirm("Are you sure you want to delete this day?")){
        window.location.href = '/delete/' + ID;
    }
}

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


