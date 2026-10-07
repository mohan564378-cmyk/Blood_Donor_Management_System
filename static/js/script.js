document.addEventListener("DOMContentLoaded", function () {

    console.log(
        "Blood Donor Management System loaded successfully."
    );


    const alerts =
        document.querySelectorAll(".alert");


    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.opacity = "0";

            alert.style.transition =
                "opacity 0.5s ease";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 4000);

    });


    const forms =
        document.querySelectorAll("form");


    forms.forEach(function (form) {

        form.addEventListener("submit", function () {

            const button =
                form.querySelector("button[type='submit']");

            if (button) {

                button.disabled = true;

                button.innerText =
                    "Processing...";

            }

        });

    });

});