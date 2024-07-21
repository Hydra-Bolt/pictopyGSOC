// Initialize variables
let currentMediaIndex = -1;
let currentMediaArray = [];
let currentMediaTypesArray = []; 
let selectedMedia = [];
let selectionMode = false;
let section = "";
let groupBy = "";
let openedGroup = "";

// Initial data display
displayData("img", "directory");

// Fetch data from a route
async function readRoute(route) {
    try {
        const response = await fetch(route);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Failed to fetch data from ${route}:`, error);
        return null;
    }
}

// Get thumbnail URL based on the media type
async function getThumbnail(path, type) {
    if (type === 'vid') {
        return `/thumbnail${path}`;
    } else {
        return `/media${path}`;
    }
}

// Fetch thumbnails for a list of paths and types
async function fetchThumbnails(paths, types) {
    const thumbnailsPromises = paths.map(async (path, index) => {
        const fileType = types[index];
        return getThumbnail(path, fileType); 
    });

    return await Promise.all(thumbnailsPromises);
}

// Create a card element
function createCard(type, thumbnailSrc, altText, name = '') {
    const card = document.createElement('div');
    card.className = 'card';

    if (type === 'group') {
        card.classList.add('group');
        card.innerHTML = `
            <img src="${thumbnailSrc}" alt="${altText}" class="thumbnail">
            <div class="group-name">${name}</div>
        `;
    } else {
        card.innerHTML = `
            <img src="${thumbnailSrc}" alt="${altText}" class="thumbnail">
        `;
    }

    return card;
}

// Display group cards with data
async function displayData(_section, _groupBy) {
    section = _section
    groupBy = _groupBy
    const data = await readRoute(`/${section}/${groupBy}`);
    const container = document.getElementById('dataContainer');
    
    if (!data || !container) {
        if (container) container.textContent = 'Failed to fetch data.';
        return;
    }

    container.innerHTML = '';

    for (const [groupName, paths, types] of data) {
        const pathsArray = paths.split(',').map(s => s.trim());
        const typesArray = types.split(',').map(s => s.trim());

        const thumbnails = await fetchThumbnails(pathsArray, typesArray);

        const groupCard = createCard('group', thumbnails[0], groupName, groupName);
        groupCard.addEventListener('click', () => {
            if (selectionMode) {
                toggleGroupSelection(pathsArray);
            } else {
                displayGroup(groupName, pathsArray, typesArray);
            }
        });
        container.appendChild(groupCard);
        if (openedGroup === groupName) {
            displayGroup(groupName, pathsArray, typesArray);
        }
    }
}

// Display media cards within a group
async function displayGroup(groupName, pathsArray, typesArray) {
    openedGroup = groupName;
    const container = document.getElementById('dataContainer');
    
    if (!container) {
        console.error('Container element not found');
        return;
    }

    container.innerHTML = '';

    for (let i = 0; i < pathsArray.length; i++) {
        const path = pathsArray[i].trim();
        const fileType = typesArray[i];
        const thumbnail = await getThumbnail(path, fileType); 

        const mediaCard = createCard('media', thumbnail, groupName);
        mediaCard.addEventListener('click', () => {
            if (selectionMode) {
                toggleMediaSelection(path);
            } else {
                openMedia(pathsArray, i, typesArray);
            }
        });
        container.appendChild(mediaCard);
    }
}

// Open a media file in a floating window
function openMedia(mediaArray, mediaIndex, typesArray) {
    currentMediaArray = mediaArray;
    currentMediaIndex = mediaIndex;
    currentMediaTypesArray = typesArray; 

    const mediaUrl = `/media${currentMediaArray[currentMediaIndex]}`;
    const mediaType = currentMediaTypesArray[currentMediaIndex]; 
    const mediaContent = document.getElementById('mediaContent');
    const floatingWindow = document.getElementById('floatingWindow');

    if (mediaType === 'vid') {
        mediaContent.innerHTML = `<video src="${mediaUrl}" controls autoplay style="max-width: 100%; max-height: 100%;"></video>`;
    } else {
        mediaContent.innerHTML = `<img src="${mediaUrl}" alt="Media" style="max-width: 100%; max-height: 100%;">`;
    }

    floatingWindow.style.display = 'block';
}

// Close the floating media window
function closeMedia() {
    const floatingWindow = document.getElementById('floatingWindow');
    floatingWindow.style.display = 'none';
    document.getElementById('mediaContent').innerHTML = '';
}

// Navigate to the previous media item
function prevMedia() {
    if (currentMediaIndex > 0) {
        openMedia(currentMediaArray, currentMediaIndex - 1, currentMediaTypesArray);
    }
}

// Navigate to the next media item
function nextMedia() {
    if (currentMediaIndex < currentMediaArray.length - 1) {
        openMedia(currentMediaArray, currentMediaIndex + 1, currentMediaTypesArray);
    }
}

// Toggle grouping of media by directory or class
function toggleGroup() {
    groupBy = groupBy === "directory" ? "class" : "directory";
    displayData(section, groupBy);
}

// Toggle between displaying images and videos
function toggleSection() {
    section = section === "img" ? "vid" : "img";
    displayData(section, groupBy);
}

// Display images based on the current section and grouping
function displayImages() {
    displayData("/img/directory");
}

// Display videos based on the current section and grouping
function displayVideos() {
    displayData("/vid/directory");
}

// Toggle selection mode
function toggleSelectionMode() {
    selectionMode = !selectionMode;
    if (selectionMode) {
        console.log('Selection mode activated');
    } else {
        selectedMedia = [];
        console.log('Selection mode deactivated');
    }
}

// Toggle selection of a single media file
function toggleMediaSelection(path) {
    const index = selectedMedia.indexOf(path);
    if (index === -1) {
        selectedMedia.push(path);
        console.log('Selected media:', path);
    } else {
        selectedMedia.splice(index, 1);
        console.log('Deselected media:', path);
    }
}

// Toggle selection of all media files in a group
function toggleGroupSelection(pathsArray) {
    let allSelected = true;
    pathsArray.forEach(path => {
        if (!selectedMedia.includes(path)) {
            allSelected = false;
        }
    });

    if (allSelected) {
        pathsArray.forEach(path => {
            const index = selectedMedia.indexOf(path);
            if (index !== -1) {
                selectedMedia.splice(index, 1);
                console.log('Deselected media:', path);
            }
        });
    } else {
        // Select all if not all are selected
        pathsArray.forEach(path => {
            if (!selectedMedia.includes(path)) {
                selectedMedia.push(path);
                console.log('Selected media:', path);
            }
        });
    }
}

// Send selected media to the backend via POST request
async function sendSelectedMedia(route) {
    try {
        const response = await fetch(route, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ selectedMedia: selectedMedia })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Server response:', result);
        displayData(section, groupBy);
        return result;
    } catch (error) {
        console.error('Failed to send data:', error);
    }
}
