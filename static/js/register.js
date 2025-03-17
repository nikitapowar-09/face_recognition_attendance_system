const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startCaptureBtn = document.getElementById('start-capture-btn');
const captureImageBtn = document.getElementById('capture-image-btn');
const registrationForm = document.getElementById('registration-form');
const registerStatus = document.getElementById('register-status');

// Handle Registration Form Submission
registrationForm.addEventListener('submit', (event) => {
  event.preventDefault(); // Prevent form from submitting normally

  // Form field validation
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const phone = document.getElementById('phone').value;

  // Validate Name
  if (!name) {
    registerStatus.textContent = "Please enter your full name.";
    registerStatus.style.color = "red";
    return;
  }

  // Validate Email
  const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
  if (!emailPattern.test(email)) {
    registerStatus.textContent = "Please enter a valid email address.";
    registerStatus.style.color = "red";
    return;
  }

  // Validate Phone Number
  const phonePattern = /^\d{10}$/;
  if (!phonePattern.test(phone)) {
    registerStatus.textContent = "Please enter a valid 10-digit phone number.";
    registerStatus.style.color = "red";
    return;
  }

  registerStatus.textContent = "All fields are valid! You can now register.";
  registerStatus.style.color = "green";
});

// Start Camera when Start Camera button is clicked
startCaptureBtn.addEventListener('click', async () => {
  // Validate fields before starting camera
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const phone = document.getElementById('phone').value;

  // Check if all fields are valid before enabling the camera
  const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
  const phonePattern = /^\d{10}$/;
  if (!name || !emailPattern.test(email) || !phonePattern.test(phone)) {
    registerStatus.textContent = "Please fill out all fields correctly before starting the camera.";
    registerStatus.style.color = "red";
    return;
  }

  registerStatus.textContent = "Starting camera for registration...";

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    video.style.display = 'block';
    captureImageBtn.style.display = 'block'; // Show Capture Image button

    // Capture face when the button is clicked
    captureImageBtn.onclick = () => {
      const context = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Stop video stream
      const tracks = stream.getTracks();
      tracks.forEach(track => track.stop());
      video.style.display = 'none';
      captureImageBtn.style.display = 'none';

      registerStatus.textContent = "Face captured successfully! Registration complete.";
      registerStatus.style.color = "green";
    };
  } catch (error) {
    console.error("Error accessing camera:", error);
    registerStatus.textContent = "Error accessing camera. Please check your permissions.";
    registerStatus.style.color = "red";
  }
});
