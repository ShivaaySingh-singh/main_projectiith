(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {

        var jQ = django.jQuery;

        
        var roleField = jQ('#id_role');
        var facultyInline = jQ('#faculty-heading').parent();
        function toggleFacultyInline(role) {
            if (role === 'faculty') {
                facultyInline.show();
            } else {
                facultyInline.hide();
            }
        }
    

        toggleFacultyInline(roleField.val());

        roleField.on('change', function() {
            toggleFacultyInline(jQ(this).val());

       });
    });

})();