
function MarkovModel() {
    this.states = {}
    this.state = ["\n"]
}

MarkovModel.prototype.addSample = function(state, followup) {
    if (!this.states.hasOwnProperty(state)) {
        this.states[state] = []
    }
    this.states[state].push(followup);
}

MarkovModel.prototype.startIteration = function() {
    this.state = ["\n"]
}

MarkovModel.prototype.next = function() {
    var options = this.states[this.state.join(' ')];
    var followup = draw(options);
    var oldstate = this.state.join(" ");
    this.state = this.state.concat(followup)
    while (this.state.length > 3) {
        this.state.shift();
    }
    console.log('"' + oldstate + '" -> "' + followup.join(' ') + '", "' + this.state.join(" ") + '"');
    return {'taken': followup, 'options': options};
}

function randomInt(minIncl, maxExcl) {
	return minIncl + Math.floor(Math.random() * (maxExcl - minIncl));
}

function draw(list) {
	var x = randomInt(0, list.length);
	return list[x];
}