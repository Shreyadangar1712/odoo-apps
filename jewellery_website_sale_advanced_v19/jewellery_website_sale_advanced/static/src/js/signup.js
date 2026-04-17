/** @odoo-module **/

console.log("jewellery_website_sale_advanced pincode js loaded");

document.addEventListener("click", async function (ev) {
    const btn = ev.target.closest("#check");
    if (!btn) {
        return;
    }

    ev.preventDefault();
    ev.stopPropagation();

    console.log("check button clicked");

    try {
        const pincodeInput = document.querySelector("#area_pincode");
        const messageBox = document.querySelector("#message_response");

        console.log("pincodeInput:", pincodeInput);
        console.log("messageBox:", messageBox);

        if (!pincodeInput || !messageBox) {
            console.warn("Required DOM elements not found.");
            return;
        }

        const pincode = (pincodeInput.value || "").trim();
        console.log("pincode:", pincode);

        if (!pincode || pincode.length !== 6 || !/^\d{6}$/.test(pincode)) {
            messageBox.textContent = "Please enter 6 digit of your area pincode";
            return;
        }

        messageBox.textContent = "Checking...";

        const response = await fetch("/process-data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ value: pincode }),
        });

        console.log("response status:", response.status);

        const data = await response.json();
        console.log("response data:", data);

        messageBox.textContent = data.message || "No response received.";
    } catch (error) {
        console.error("Error fetching pincode data:", error);
        const messageBox = document.querySelector("#message_response");
        if (messageBox) {
            messageBox.textContent = "Something went wrong. Please try again.";
        }
    }
});