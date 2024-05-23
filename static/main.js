// constants
BASE_API = "https://pokeapi.co/api/v2/";
const input = document.querySelector("#pokemon-search");
const suggestions = document.querySelector(".suggestions ul");
const searchForm = document.querySelector("#search-form");
const pkmnTeamDiv = document.querySelector("#pokemon-team-div");
const finishTeamBtn = document.querySelector("#finish-team");

// global vars
let pkmnList;
let pkmnNameList = [];
let pkmnTeam = [];
let numPkmn = 0;

/* 
    Search bar functions
*/

/**
 * 
 * @param {String} str - takes string of text the user has inputed
 * so far into the search box
 * @returns {Array} - array of search results
 */
function search(str) {
    // returns array of search results
    let results = [];
    results = pkmnNameList.filter(val => {
        return val.toLowerCase().includes(str.toLowerCase());
    });
    return results;
}

/**
 * function to remove ils when appropriate (say when the il contains
 * a word that no longer matches the search)
 */
function hideSuggestions() {
    while (suggestions.firstChild) {
        suggestions.removeChild(suggestions.firstChild);
    }
}

/**
 * 
 * @param {Event} e 
 * Adds ils under the search bar as the user is typing
 */
function searchHandler(e) {
    showSuggestions(search(input.value), input.value);
}

/**
 * 
 * @param {Array} results 
 * @param {String} inputVal 
 * Creates ils with words that match what the user is searching
 * and adds it to the results array
 */
function showSuggestions(results, inputVal) {
    hideSuggestions();

    if (inputVal === "") {
        return;
    }

    results.forEach(val => {
        const newLi = document.createElement("li");
        newLi.innerText = val;
        suggestions.append(newLi);
    });
}

/**
 * 
 * @param {Event} e 
 * Once a user clicks on a suggestion il, fill the search bar
 * with the suggestion
 */
function useSuggestions(e) {
    if (e.target.tagName == "LI") {
        input.value = e.target.innerText;
        hideSuggestions();
    }
}

/*
    event listeners for adding a new character into the search bar
    and clicking on a suggestion
*/
input.addEventListener('keyup', searchHandler);
suggestions.addEventListener('click', useSuggestions);


/* 
    Pokemon Team Functions
*/

/**
 * Gets the list of all pokemon
 * @returns json response data from the Pokeapi api
 */
async function getPokemonList() {
    // limit is 1350 because there are only about 1300 pokemon
    response = await axios.get(`${BASE_API}/pokemon?limit=1350`);
    return response;
}

/**
 * Creates a json object with name:url and add it to global pkmnTeam arr
 * @param {String} name 
 * @param {String} url 
 */
function addPokemonToTeam(name, url) {
    let singlePkmn = [];
    singlePkmn[0] = name;
    singlePkmn[1] = url;
    console.log(singlePkmn);
    pkmnTeam.push(singlePkmn);
}

/** 
 * When the finish team button is clicked, send the array of
 * json objects containing Pokemon team data to the route
 * /teams/new and then refresh the page.
 */
finishTeamBtn.addEventListener("click", async function(e) {
    e.preventDefault();
    if (numPkmn === 0) {
        alert("Please add at least one Pokemon!");
        return -1;
    }
    for (let i = pkmnTeam.length; i < 6; i++) {
        pkmnTeam.push(["",""]);
    }
    await axios.post("/teams/new", pkmnTeam);
    console.debug("DEBUG: sent team to server");
    location.reload();
});

/**
 * Fills the pkmnNameList with the names of all pokememon
 * @param {Array} pkmnList 
 * @returns {Array} pkmnNameList
 */
function getPokemonNameList(pkmnList) {
    let pkmnNameList = [];
    let names = pkmnList.data.results;
    for (let i = 0; i < names.length; i++) {
        pkmnNameList.push(names[i].name);
    }
    return pkmnNameList;
}

/**
 * Finds the pokemon's associates url which contains sprite information
 * as well as other info
 * @param {String} pkmnName 
 * @returns {String} the url associates with the pokemon
 */
function searchForURL(pkmnName) {
    let pkmnURL;
    if (pkmnNameList.indexOf(pkmnName) === -1) {
        return -1;
    }
    
    for (let i = 0; i < pkmnList.data.results.length; i++) {
        if (pkmnList.data.results[i].name === pkmnName) {
            pkmnURL = pkmnList.data.results[i].url;
        }
    }

    return pkmnURL;
}

/**
 * uses the associated url to get the front facing sprite (image)
 * @param {String} pkmnURL 
 * @returns {String} the sprite url
 */
async function getPokemonSprite(pkmnURL) {
    let response = await axios.get(pkmnURL);
    return response.data.sprites.front_default;
}

/**
 * Adds the searched pokemon to a temporary list of cards that
 * show the pokemon name and picture. Checks that the pokemon
 * being added is valid and that there are less than six.
 */
searchForm.addEventListener("submit", async function(e) {
    // adds a pokemon to the temporary list
    e.preventDefault();
    if (numPkmn === 6) {
        alert("Max six Pokemon in a team!");
        return -1;
    }
    let pkmnName = input.value;
    let pkmnURL = searchForURL(pkmnName);
    if (pkmnURL === -1) {
        alert("Incorrect Pokemon name, try again");
    }
    else {
        let spriteURL = await getPokemonSprite(pkmnURL);
        newDiv = document.createElement("div");
        newDiv.classList.add("card");
        newDiv.innerHTML += `<div>${pkmnName}</div>`;
        newDiv.innerHTML += `<img src="${spriteURL}" alt="${pkmnName}">`;
        pkmnTeamDiv.appendChild(newDiv);
        addPokemonToTeam(pkmnName, spriteURL);
        numPkmn++;
    }
    input.value = "";
});

/* 
    Starting function
*/

/**
 * Function runs once the DOM content on the page loads.
 * Retrieves a list of all pokemon and saves their names
 * so they can be used later.
 */
async function start() {
    console.debug("DEBUG: finished loading");
    pkmnList = await getPokemonList();
    pkmnNameList = getPokemonNameList(pkmnList);
}

// event listener that waits for dom content to be loaded
document.addEventListener("DOMContentLoaded", start);