const themeButton = document.querySelector('.theme-button');
themeButton.addEventListener('click', () => document.body.classList.toggle('dark'));

const date = new Date();
document.querySelector('#today').textContent = date.toLocaleDateString('en-GB', {
  weekday: 'long', day: 'numeric', month: 'long'
}) + ' at ' + date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
