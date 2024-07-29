// script.js
document.addEventListener('DOMContentLoaded', function() {
    const element = document.getElementById('animated-text');
    const texts = ["Match the mood", "Match the day", "Match the song"];
    let index = 0;
    let text = texts[index];
    
    function animateText() {
        element.textContent = text;
        element.style.animation = 'typing 1s steps(20, end), cursor-blink 0.75s step-end infinite';
        
        setTimeout(() => {
            element.style.animation = 'erase 1s steps(20, end), cursor-blink 0.75s step-end infinite';
            
            setTimeout(() => {
                index = (index + 1) % texts.length;
                text = texts[index];
                animateText();
            }, 1000); // Duration of erasing animation
        }, 1000); // Duration of typing animation
    }
    
    animateText();
});
