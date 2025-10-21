document.addEventListener("DOMContentLoaded", function () {
    function recalc(row) {
        let opening = parseFloat(row.querySelector('[name$="opening_balance"]').value) || 0;
        let receipt = parseFloat(row.querySelector('[name$="receipt"]').value) || 0;
        let payments = parseFloat(row.querySelector('[name$="payments"]').value) || 0;
        let presentBill = parseFloat(row.querySelector('[name$="present_bill"]').value) || 0;

        let total = opening + receipt;
        let balanceAfter = (parseFloat(row.querySelector('[name$="sanction_amount"]').value) || 0) - payments;
        let balance = total - payments - presentBill;

        row.querySelector('.field-total input').value = total.toFixed(2);
        row.querySelector('.field-balance_after_payment input').value = balanceAfter.toFixed(2);
        row.querySelector('.field-balance input').value = balance.toFixed(2);
    }

    document.querySelectorAll("tr.has_original").forEach(function (row) {
        row.querySelectorAll("input").forEach(function (input) {
            input.addEventListener("input", function () {
                recalc(row);
            });
        });
    });
});
