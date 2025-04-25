// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Handle account balance updates
    const updateBalance = (accountId, newBalance) => {
        const balanceElement = document.querySelector(`#account-${accountId} .balance`);
        if (balanceElement) {
            balanceElement.textContent = `$${parseFloat(newBalance).toFixed(2)}`;
        }
    };

    // Handle form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Handle real-time amount calculation
    const amountInput = document.querySelector('#amount');
    if (amountInput) {
        amountInput.addEventListener('input', function() {
            const amount = parseFloat(this.value) || 0;
            const formattedAmount = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'INR'
            }).format(amount);
            
            const amountDisplay = document.querySelector('#amount-display');
            if (amountDisplay) {
                amountDisplay.textContent = formattedAmount;
            }
        });
    }

    // Handle account selection
    const fromAccountSelect = document.querySelector('#from_account');
    if (fromAccountSelect) {
        fromAccountSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const balance = selectedOption.getAttribute('data-balance');
            const balanceDisplay = document.querySelector('#selected-account-balance');
            if (balanceDisplay) {
                balanceDisplay.textContent = `Available Balance: $${parseFloat(balance).toFixed(2)}`;
            }
        });
    }

    // Handle transaction search
    const searchInput = document.querySelector('#transaction-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const transactions = document.querySelectorAll('.transaction-item');
            
            transactions.forEach(transaction => {
                const text = transaction.textContent.toLowerCase();
                transaction.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Handle date range filter
    const dateRangeInput = document.querySelector('#date-range');
    if (dateRangeInput) {
        dateRangeInput.addEventListener('change', function() {
            const [startDate, endDate] = this.value.split(' - ');
            const transactions = document.querySelectorAll('.transaction-item');
            
            transactions.forEach(transaction => {
                const date = transaction.getAttribute('data-date');
                const isInRange = date >= startDate && date <= endDate;
                transaction.style.display = isInRange ? '' : 'none';
            });
        });
    }

    // Handle chart responsiveness
    const charts = document.querySelectorAll('canvas');
    charts.forEach(chart => {
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const canvas = entry.target;
                const chartInstance = Chart.getChart(canvas);
                if (chartInstance) {
                    chartInstance.resize();
                }
            }
        });
        resizeObserver.observe(chart);
    });

    // Add loading states to buttons
    const buttons = document.querySelectorAll('button[type="submit"]');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                this.disabled = true;
            }
        });
    });
});

// Utility Functions
const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
};

const formatDate = (date) => {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
};

// API Functions
const fetchTransactions = async (accountId) => {
    try {
        const response = await fetch(`/api/transactions/${accountId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching transactions:', error);
        return [];
    }
};

const fetchAccountBalance = async (accountId) => {
    try {
        const response = await fetch(`/api/accounts/${accountId}/balance`);
        const data = await response.json();
        return data.balance;
    } catch (error) {
        console.error('Error fetching account balance:', error);
        return 0;
    }
}; 
function numberonly(input)
{   
    var num = /[^0-9]/gi;//field which is allowed in that particular input field
    input.value=input.value.replace(num,"");//replaces characters other than number with a space or blank 
    //short hand but above one is easy to understand
    //input.value = value.replace(/[^0-9]/g, '');

    var number = document.getElementById("number").value;
    var number_text = document.getElementById("verify_number");
    var numlength = number.length;
    let a = 10;

    if(numlength != (a) && numlength != 0)
    {
        number_text.innerHTML = "Please Enter 10 digit Phone-Number"
        number_text.style.color = "#ff0000";
    }
    else{
        number_text.innerHTML ="Valid 10 digit Phone-Number"
        number_text.style.color = "#00ff00";
    }
    //if the phone section is empty
    if (number == ""){
        number_text.innerHTML = "";
    }
}

//this function for alphabets only
function alphabetonly(input)
{
    var alpha = /[^a-zA-z]/gi;// gi is a flags that tells the function to look for match over the entire string (will otherwise break at the first match), this is the "g" flag. And the "i" flag tells it to match case insensitively.
    input.value=input.value.replace(alpha,"");    // Remove any non-alphabetic characters
    //short hand
    //input.value = value.replace(/[^a-zA-Z]/g, '');
}

//this function is to verify email
function verifyemail(){
    //var form = document.getElementById("form")
    var email = document.getElementById("email").value;
    var text = document.getElementById("verify_email");
    var pattern = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;

    if (email.match(pattern))
    {
        text.innerHTML = "Your Email Address is valid";
        text.style.color = "#00ff00";
    }
    else{
        text.innerHTML = "Please enter valid Email Address";
        text.style.color = "#ff0000";
    }
    //if the email section is empty
    if (email== "") {
        text.innerHTML = "";      
    }
}

document.getElementById('loadingvs').addEventListener('submit', function() {
    document.getElementById('loader').style.display = 'flex';
});

