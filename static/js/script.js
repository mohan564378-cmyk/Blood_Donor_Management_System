document.addEventListener("DOMContentLoaded", function () {

    const flashMessages =
        document.querySelectorAll(".flash-message");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.classList.add("hide");

        }, 4000);

    });


    const deleteLinks =
        document.querySelectorAll(
            ".delete-link"
        );

    deleteLinks.forEach(function (link) {

        link.addEventListener("click", function (event) {

            const confirmed = confirm(
                "Are you sure you want to delete this item?"
            );

            if (!confirmed) {

                event.preventDefault();

            }

        });

    });


    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function () {

                const button =
                    form.querySelector(
                        "button[type='submit']"
                    );

                if (button) {

                    button.classList.add(
                        "loading"
                    );

                }

            }
        );

    });


    const mobileButton =
        document.querySelector(".mobile-menu-button");

    const navigation =
        document.querySelector(".nav-links");

    if (mobileButton && navigation) {

        mobileButton.addEventListener(
            "click",
            function () {

                navigation.classList.toggle(
                    "mobile-active"
                );

            }
        );

    }


    const ageInputs =
        document.querySelectorAll(
            "input[name='age']"
        );

    ageInputs.forEach(function (input) {

        input.addEventListener(
            "input",
            function () {

                if (Number(this.value) < 18) {

                    this.setCustomValidity(
                        "Donor age must be at least 18."
                    );

                } else if (Number(this.value) > 65) {

                    this.setCustomValidity(
                        "Please enter a valid age."
                    );

                } else {

                    this.setCustomValidity("");

                }

            }
        );

    });


    const phoneInputs =
        document.querySelectorAll(
            "input[name='phone']"
        );

    phoneInputs.forEach(function (input) {

        input.addEventListener(
            "input",
            function () {

                this.value =
                    this.value.replace(
                        /[^0-9+ ]/g,
                        ""
                    );

            }
        );

    });

});