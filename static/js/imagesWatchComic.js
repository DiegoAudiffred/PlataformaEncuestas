  
  function previewImages(input) {
    const files = input.files;
    const container = document.getElementById("imagePreviewContainer");
    container.innerHTML = "";

    if (files.length === 0) return;

    for (const file of files) {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = function(e) {
          const col = document.createElement("div");
          col.className = "col-4 col-sm-3 col-md-2";
          const imgWrapper = document.createElement("div");
          imgWrapper.className = "ratio ratio-1x1 border rounded overflow-hidden shadow-sm";
          const img = document.createElement("img");
          img.src = e.target.result;
          img.style.objectFit = "cover";
          imgWrapper.appendChild(img);
          col.appendChild(imgWrapper);
          container.appendChild(col);
        };
        reader.readAsDataURL(file);
      }
    }

    const modalElement = document.getElementById("confirmUploadModal");
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
  }

  function cancelUpload() {
    const input = document.getElementById("newPagesInput");
    input.value = "";
    document.getElementById("imagePreviewContainer").innerHTML = "";
  }

  function submitUpload() {
    document.getElementById("uploadSpinner").classList.remove("d-none");
    document.getElementById("uploadText").textContent = "Subiendo...";
    document.getElementById("confirmButton").disabled = true;
    document.getElementById("uploadForm").submit();
  }

  /* <script>
  function previewImages(input) {
    const files = input.files;
    const container = document.getElementById("imagePreviewContainer");
    container.innerHTML = "";

    if (files.length === 0) return;

    for (const file of files) {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = function (e) {
          const img = document.createElement("img");
          img.src = e.target.result;
          img.style.height = "100px";
          img.style.objectFit = "cover";
          img.classList.add("rounded", "shadow");
          container.appendChild(img);
        };
        reader.readAsDataURL(file);
      }
    }

    const modal = new bootstrap.Modal(document.getElementById("confirmUploadModal"));
    modal.show();
  }

  function cancelUpload() {
    const input = document.getElementById("newPagesInput");
    input.value = "";
    document.getElementById("imagePreviewContainer").innerHTML = "";
  }

  function submitUpload() {
    document.getElementById("uploadSpinner").classList.remove("d-none");
    document.getElementById("uploadText").textContent = "Subiendo...";
    document.getElementById("confirmButton").disabled = true;

    document.getElementById("uploadForm").submit();
  }
</script>
 */