function PlaylistsByDate(wrapper, content) {
    // an estimate of how much space each day takes
    this.spacePerDay = 535;

    // number of days to display each time we scroll
    this.displayDays = 5;

    // days of overlap on each side
    this.overlapDays = 1;

    // we subtract these so the current day is really the last overlap day
    this.absoluteEnd = moment().endOf('day').subtract(this.overlapDays, 'days');

    // TODO: pull this from the database?
    this.absoluteStart = moment("2007-09-07");

    // leave these alone
    this.displayEnd = this.absoluteEnd;
    this.displayStart = null;
    this.padTop = 0;
    this.padBottom = 0;
    this.scrollTop = 0;

    this.wrapper = wrapper;
    this.content = content;
}

PlaylistsByDate.prototype.updateData = function(end, direction) {
    direction = typeof direction !== 'undefined' ? direction : null;

    var dates = [];
    for(var i = -this.overlapDays; i < this.displayDays + this.overlapDays; i++) {
        var dt = moment(end).subtract(i, 'days');

        // don't display days earlier than the start
        if(dt >= this.absoluteStart) {
            dates.push(dt.startOf('day'));
        }
    }

    this.displayStart = dates[dates.length - 1];
    this.displayEnd = dates[0].endOf('day');

    //console.log("displayStart: " + this.displayStart.format());
    //console.log("displayEnd: " + this.displayEnd.format());

    $.ajax({
        'url': '/playlists/date/data?start=' + this.displayStart.toISOString() + '&end=' + this.displayEnd.toISOString(),
        'dataType': 'json',
        'context': this,
    }).done(function(data) {
        var sets = data['sets'];
        var days = {};

        for(i in sets) {
            var key = moment(sets[i]['dtstart']).startOf('day');
            if(key in days) {
                days[key].push(sets[i]);
            }
            else {
                days[key] = [sets[i]];
            }
        }

        if(direction == 'down') {
            // save current height and add it to top padding
            //console.log("direction: down");
            this.padTop += $(this.content).height();

            // deal with overlapping days
            for(var i = 0; i < this.overlapDays; i++) {
                this.padTop -= $(this.content + ' section').eq(-i).height();
            }
        }

        // remove existing data
        $(this.content).html('');

        for(date in days) {
            var head = document.createElement('header');
            $(head).text(moment(date).format('dddd, MMMM D, YYYY'));

            var list = document.createElement('ul');
            $.each(days[date], function(index, value) {
                var link = document.createElement('a');
                link.href = '/playlists/set/' + value['id'];
                $(link).text(moment(value['dtstart']).format('HH:mm') + "-" + moment(value['dtend']).format('HH:mm') + ": " + value['dj']['airname']);
                makeAjaxLink(link);

                var li = document.createElement('li');
                $(li).append(link);
                $(list).append(li);
            });

            var section = document.createElement('section');
            $(section).append(head);
            $(section).append(list);
            $(this.content).append(section);
        }

        if(direction == 'up') {
            // subtract current height from top padding
            //console.log("direction: up");
            this.padTop -= $(this.content).height();

            // deal with overlapping days
            for(var i = 0; i < this.overlapDays; i++) {
                this.padTop += $(this.content + ' section').eq(i).height();
            }

            if(this.padTop < 0) {
                this.padTop = 0;
                this.scrollTop = 0;
            }
            else {
                this.scrollTop = this.padTop;
            }
        }

        $(this.content).css('padding-top', this.padTop + 'px');
    });
}

PlaylistsByDate.prototype.jumpToDate = function(dt) {
    if(dt < this.absoluteStart) {
        dt = this.absoluteStart;
    }

    this.padTop = moment(this.absoluteEnd).diff(dt, 'days') * this.spacePerDay;
    this.scrollTop = this.padTop;

    // our jump to date is the end of the current day, minus overlapping days
    dt = dt.endOf('day').subtract(this.overlapDays, 'days');
    this.updateData(dt);

    $(this.wrapper).animate({'scrollTop': this.padTop}, 500);
}

PlaylistsByDate.prototype.handleScroll = function(ev) {
    var newEnd;
    var inst = ev.data.instance;

    // TODO: add a timeout for these bits

    if(!$(this).is(':animated')) {
        if($(this).scrollTop() + $(this).innerHeight() < inst.scrollTop) {
            newEnd = moment(inst.displayStart).add(inst.displayDays * 2 + inst.overlapDays, 'days');
            if(newEnd >= inst.absoluteEnd) {
                newEnd = inst.absoluteEnd;
            }

            inst.updateData(newEnd, 'up');
        }
        else if($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            newEnd = moment(inst.displayStart).subtract(1, 'days');
            if(newEnd > inst.absoluteStart) {
                inst.updateData(newEnd, 'down');
                inst.scrollTop = $(this).scrollTop() - 1;
            }
        }
    }
}

PlaylistsByDate.prototype.init = function() {
    $(this.wrapper).bind('scroll', {'instance': this}, this.handleScroll);
    $('#date_jump_form').bind('submit', {'instance': this}, function(ev) {
        ev.data.instance.jumpToDate(moment($('#date_entry').val()));
        return false;
    });

    this.updateData(this.absoluteEnd);
}
