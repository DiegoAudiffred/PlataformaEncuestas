
  function setupTagInput({ inputId, suggestionsId, containerId, hiddenInputId }) {
    const tagInput = document.getElementById(inputId);
    const tagSuggestions = document.getElementById(suggestionsId);
    const tagContainer = document.getElementById(containerId);
    const tagsSelectedInput = document.getElementById(hiddenInputId);

    let selectedTags = [];
    let selectedIndex = -1;

    function loadTags(existingTags) {
      selectedTags = existingTags.split(",").filter(tag => tag.trim() !== "");
      renderTags();
    }

    function renderTags() {
      tagContainer.innerHTML = '';  
      selectedTags.forEach(tag => {
        const tagDiv = document.createElement("div");
        tagDiv.className = "badge bg-secondary text-white rounded-pill px-3 py-2 d-flex align-items-center gap-2";
        tagDiv.innerHTML = `
                    ${tag}
                    <button type="button" class="btn-close btn-close-white btn-sm ms-2" aria-label="Remove"></button>
                `;

        tagDiv.querySelector("button").addEventListener("click", () => {
          removeTag(tag);
        });

        tagContainer.appendChild(tagDiv);
      });
      updateHiddenInput();
    }

    const existingTags = tagsSelectedInput.value; 
    loadTags(existingTags);

    tagInput.addEventListener("input", async () => {
      const query = tagInput.value.trim();
      const terms = query.split(" ");
      const lastTerm = terms[terms.length - 1];

      if (lastTerm.length < 1) {
        tagSuggestions.classList.add("d-none");
        tagSuggestions.innerHTML = "";
        selectedIndex = -1;
        return;
      }

      const response = await fetch(`/tags-suggest/?q=${encodeURIComponent(lastTerm)}`);
      const tags = await response.json();

      tagSuggestions.innerHTML = "";
      if (tags.length > 0) {
        tagSuggestions.innerHTML = tags.map(tag => `
                    <div class="p-2 suggestion-item" style="cursor:pointer;">
                        ${tag}
                    </div>
                `).join('');

        tagSuggestions.classList.remove("d-none");

        document.querySelectorAll(`#${suggestionsId} .suggestion-item`).forEach((item, index) => {
          item.addEventListener("click", () => {
            addTag(item.textContent);
            tagInput.value = "";
            tagSuggestions.classList.add("d-none");
            selectedIndex = -1;
            tagInput.focus();
          });
        });

        selectedIndex = -1;
      } else {
        tagSuggestions.classList.add("d-none");
      }
    });

    tagInput.addEventListener("keydown", e => {
      const suggestions = tagSuggestions.querySelectorAll(".suggestion-item");

      if (e.key === "ArrowDown") {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % suggestions.length;
        updateActiveSuggestion(suggestions);
      }
      else if (e.key === "ArrowUp") {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + suggestions.length) % suggestions.length;
        updateActiveSuggestion(suggestions);
      }
      else if (e.key === "Tab") {
        if (suggestions.length > 0) {
          e.preventDefault();
          const idx = selectedIndex >= 0 ? selectedIndex : 0;
          addTag(suggestions[idx].textContent);
          tagInput.value = "";
          tagSuggestions.classList.add("d-none");
          selectedIndex = -1;
        }
      }
      else if (e.key === "Enter") {
        e.preventDefault();
        if (suggestions.length > 0 && selectedIndex >= 0) {
          addTag(suggestions[selectedIndex].textContent);
        } else if (tagInput.value.trim() !== "") {
          addTag(tagInput.value.trim());
        }
        tagInput.value = "";
        tagSuggestions.classList.add("d-none");
        selectedIndex = -1;
      }
    });

    function updateActiveSuggestion(suggestions) {
      suggestions.forEach((item, index) => {
        if (index === selectedIndex) {
          item.classList.add("bg-light", "active");
          item.scrollIntoView({ block: "nearest" });
        } else {
          item.classList.remove("bg-light", "active");
        }
      });
    }

    function addTag(tagText) {
      const cleanTag = tagText.trim();
      if (cleanTag === "" || selectedTags.includes(cleanTag)) return;

      selectedTags.push(cleanTag);

      const tagDiv = document.createElement("div");
      tagDiv.className = "badge bg-secondary text-white rounded-pill px-3 py-2 d-flex align-items-center gap-2";
      tagDiv.innerHTML = `
                ${cleanTag}
                <button type="button" class="btn-close btn-close-white btn-sm ms-2" aria-label="Remove"></button>
            `;

      tagDiv.querySelector("button").addEventListener("click", () => {
        tagContainer.removeChild(tagDiv);
        selectedTags = selectedTags.filter(t => t !== cleanTag);
        updateHiddenInput();
      });

      tagContainer.appendChild(tagDiv);
      updateHiddenInput();
    }

    function updateHiddenInput() {
      tagsSelectedInput.value = selectedTags.join(",");
    }

  }

  setupTagInput({
    inputId: "tagInputArtist",
    suggestionsId: "tagSuggestionsArtist",
    containerId: "tagContainerArtist",
    hiddenInputId: "tagsSelectedArtist"
  });