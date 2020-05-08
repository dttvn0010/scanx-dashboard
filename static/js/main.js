$(document).ready(function(){
    $('.table-form input,textarea,select').each(function(){
        $(this).addClass('form-control');
    });

    $('.table-form input[type=file]').each(function(){
        $(this).removeClass('form-control');
        $(this).addClass('form-control-file');
    });

    $('.table-form input[type=checkbox]').each(function(){
      $(this).removeClass('form-control');
  });
});

function confirmDelete(a) {
  var url = a.getAttribute('url');
  if (confirm('Do you want to delete?')) {
    location.href = url;
  }
}