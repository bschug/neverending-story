function getStoryUrl() {
    if (window.location.hash.length > 1) {
        return 'models/' + window.location.hash.substr(1) + '.bz2';
    }
    return "models/model.bz2";
}

function loadCompressedJSON(url, callback) {
    console.log("Loading compressed JSON from " + url);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'arraybuffer';
    xhr.send();
    xhr.onload = function() {
        console.log("Decompressing...");
        var compressed = new Uint8Array(xhr.response);
        console.log("Parsing JSON...")
        var json = bzip2.simple(bzip2.array(compressed));
        console.log("Done.")
        callback(JSON.parse(json));
    }
    xhr.onerror = function(error) {
        console.log("Failed to load " + url);
        console.log(error);
    }
}

function loadModel(modelUrl, callback) {
    console.log("loading model " + modelUrl + "...");
    loadCompressedJSON(modelUrl, function(states) {
        console.log("model loaded successfully");
        window.storyModel.states = states;
        window.storyModel.startIteration();
        callback();
    });
}

function tellStory(modelUrl) {
    window.storyModel = new MarkovModel();
    loadModel(modelUrl, function() {
        $("#loading").remove();
        tellNextWord();
    });
}

function tellNextWord() {
    var decision = window.storyModel.next();
    var aniElem = makeAnimationElement(decision);
    animateDecision(decision, aniElem);
    for (var i=0; i < decision.taken.length; i++) {
        addToStory(decision.taken[i]);
    }
    var lastToken = decision.taken[decision.taken.length - 1];
    //if (lastToken != '\n' && lastToken != '.') {
    //    console.log("Last token was '" + lastToken + '", scheduling next word');
    //    setTimeout(tellNextWord, 1000);
    //}
    if (decision.options.length == 1) {
        setTimeout(tellNextWord, 400);
    } else {
        setTimeout(tellNextWord, 1000);
    }
}

// Add a new word to the animation area. Remove old words as needed.
function makeAnimationElement(decision) {
    var elem = $('<div class="decision"></div>').appendTo("#animarkov-inner");
    var placeholder = createDecisionOptionElem(decision.taken, ['placeholder'])
    placeholder.classList.add("placeholder")
    elem.append(placeholder);
    while ($("#animarkov-inner").width() > $("#thestory").width()) {
        $("#animarkov-inner > .decision:first-child").remove()
    }
    return elem;
}

function animateDecision(decision, anchor) {
    // create all the elements for the options
    var optionElems = [];
    optionElems.push(createDecisionOptionElem(decision.taken));
    optionElems[0].taken = true;
    for (var i=0; i < decision.options.length; i++) {
        if (decision.options[i] == decision.taken) {
            continue;
        }
        if (optionElems.length >= 7) {
            break;
        }
        var elem = createDecisionOptionElem(decision.options[i]);
        elem.taken = false;
        optionElems.push(elem);
    }
    shuffle(optionElems);

    // Show and fan-out the possible options
    var takenIdx = null;
    var takenPos = 0;
    for (var i=0; i < optionElems.length; i++) {
        var elem = optionElems[i];
        anchor.append(elem);
        elem.style.transform = "translateY(" + (elem.offsetHeight * (i - optionElems.length/2)) + "px)";
        if (elem.taken) {
            takenIdx = i;
            takenPos = elem.offsetHeight * (i - optionElems.length/2);
        }
    }

    // Move them so that the taken option is at the right height
    setTimeout(function() {
        anchor.get(0).style.transform = "translateY(" + (-takenPos) + "px)";
    }, 500)

    // Fade in the taken option, fade out the others
    setTimeout(function() {
        for (var i=0; i < optionElems.length; i++) {
            var elem = optionElems[i];
            elem.style.color = (i === takenIdx) ? "#000000" : "#fafafa";
        }
    }, 800)
}

function addToStory(token) {
    var story = $("#thestory > p:last-child")
    var storyContainer = $("#thestory");
    var wasAtBottom = storyContainer.prop('scrollHeight') < storyContainer.scrollTop() + storyContainer.prop('clientHeight') + 5;

    if (token === '\n') {
        $('<p></p>').appendTo("#thestory")
    } else if (isPunctuation(token)) {
        story.text(story.text() + token)
    } else {
        story.text(story.text() + " " + token)
    }

    say(token);

    if (wasAtBottom) {
        storyContainer.scrollTop(storyContainer.prop('scrollHeight'));
    } else {
        console.log("was not at bottom, not autoscrolling: ", storyContainer.prop('scrollHeight'), " vs. ", storyContainer.scrollTop() + storyContainer.prop('clientHeight'));
    }
}

var isTextToSpeechEnabled = false;
function toggleTextToSpeech() {
    if (isTextToSpeechEnabled) {
        $("#textToSpeech").fadeTo(0, 0.5);
        isTextToSpeechEnabled = false;
    } else {
        $("#textToSpeech").fadeTo(0, 1);
        isTextToSpeechEnabled = true;
    }
}

var textToSpeechBuffer = "";
function say(word) {
    if (!isTextToSpeechEnabled) {
        return;
    }

    textToSpeechBuffer += " " + word;
    if (!(isPunctuation(word) || word.indexOf("\n") >= 0 || textToSpeechBuffer.length > 50)) {
        return;
    }

    if ('speechSynthesis' in window) {
        var msg = new SpeechSynthesisUtterance(textToSpeechBuffer);
        window.speechSynthesis.speak(msg);
    }
    textToSpeechBuffer = "";
}

function createDecisionOptionElem(tokens) {
	var elem = document.createElement('SPAN');
	elem.textContent = tokensToText(tokens);
	elem.classList.add('decision-option');
    elem.isPunctuation = isPunctuation(tokens[0]);
    if (elem.isPunctuation) {
        elem.classList.add("punctuation");
    }
	return elem;
}

function tokensToText(tokens) {
    var result = [];
    for (var i=0; i < tokens.length; i++) {
        var t = tokens[i];
        if (t == '\n') {
            result.push("\u21B5");
        } else if (isPunctuation(t)) {
            result.push(t);
        } else {
            result.push(" ");
            result.push(t);
        }
    }
    return result.join('');
}

function shuffle(a) {
    var j, x, i;
    for (i = a.length; i; i--) {
        j = Math.floor(Math.random() * i);
        x = a[i - 1];
        a[i - 1] = a[j];
        a[j] = x;
    }
}

function isPunctuation(token) {
    return ",.-!?:&".indexOf(token) !== -1;
}

