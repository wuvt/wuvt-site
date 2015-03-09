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

    // TODO: these should be associated with Dates and have more metadata
    var entries = [
        "17:37-18:19: <a href='https://www.wuvt.vt.edu/'>Charles in Charge</a>",
        "15:41-16:01: <a href='https://www.wuvt.vt.edu/'>Cheebee/Doctor House</a>",
        "12:11-13:42: <a href='https://www.wuvt.vt.edu/'>Pierce Sprague</a>",
        "09:29-11:17: <a href='https://www.wuvt.vt.edu/'>Bryan Hunt</a>",
        "07:14-08:40: <a href='https://www.wuvt.vt.edu/'>Jim Dubinsky</a>",
        "02:56-03:22: <a href='https://www.wuvt.vt.edu/'>The Wiggity Wack Swaggy Stack Show</a>",
        "02:47-02:49: <a href='https://www.wuvt.vt.edu/'>Easy-E</a>",
        "02:34-02:44: <a href='https://www.wuvt.vt.edu/'>Automation</a>",
        "17:37-18:19: <a href='https://www.wuvt.vt.edu/'>Charles in Charge</a>",
        "15:41-16:01: <a href='https://www.wuvt.vt.edu/'>Cheebee/Doctor House</a>",
        "12:11-13:42: <a href='https://www.wuvt.vt.edu/'>Pierce Sprague</a>",
        "09:29-11:17: <a href='https://www.wuvt.vt.edu/'>Bryan Hunt</a>",
        "07:14-08:40: <a href='https://www.wuvt.vt.edu/'>Jim Dubinsky</a>",
        "02:56-03:22: <a href='https://www.wuvt.vt.edu/'>The Wiggity Wack Swaggy Stack Show</a>",
        "02:47-02:49: <a href='https://www.wuvt.vt.edu/'>Easy-E</a>",
        "02:34-02:44: <a href='https://www.wuvt.vt.edu/'>Automation</a>",
        "17:37-18:19: <a href='https://www.wuvt.vt.edu/'>Charles in Charge</a>",
        "15:41-16:01: <a href='https://www.wuvt.vt.edu/'>Cheebee/Doctor House</a>",
        "12:11-13:42: <a href='https://www.wuvt.vt.edu/'>Pierce Sprague</a>",
        "09:29-11:17: <a href='https://www.wuvt.vt.edu/'>Bryan Hunt</a>",
        "07:14-08:40: <a href='https://www.wuvt.vt.edu/'>Jim Dubinsky</a>",
        "02:56-03:22: <a href='https://www.wuvt.vt.edu/'>The Wiggity Wack Swaggy Stack Show</a>",
        "02:47-02:49: <a href='https://www.wuvt.vt.edu/'>Easy-E</a>",
        "02:34-02:44: <a href='https://www.wuvt.vt.edu/'>Automation</a>",
    ];

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

    for(i in dates) {
        var head = document.createElement('header');
        $(head).text(dates[i].format('dddd, MMMM D, YYYY'));

        var list = document.createElement('ul');
        $.each(entries, function(index, value) {
            if(Math.random() > 0.4) {
                //var li = $('<li/>', {'text': value});
                var li = $('<li/>', {'html': value});
                $(list).append(li);
            }
        });

        /*var foot = document.createElement('footer');
        var utcDate = new Date(dates[i].getTime() + dates[i].getTimezoneOffset() * 60000);
        $(foot).text(utcDate.toISOString());*/

        var section = document.createElement('section');
        $(section).append(head);
        $(section).append(list);
        //$(section).append(foot);
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
        }
    }

    $(this.content).css('padding-top', this.padTop + 'px');
}

PlaylistsByDate.prototype.jumpToDate = function(dt) {
    if(dt < this.absoluteStart) {
        dt = this.absoluteStart;
    }

    this.padTop = moment(this.absoluteEnd).diff(dt, 'days') * this.spacePerDay;
    this.updateData(dt);

    $(this.wrapper).unbind('scroll');
    $(this.wrapper).animate(
        {
            'scrollTop': $(this.content + ' section:eq(1)').offset().top,
        },
        500, function() {
            $(this.wrapper).bind('scroll', {'instance': this}, this.handleScroll);
        });
}

PlaylistsByDate.prototype.handleScroll = function(ev) {
    // TODO: add a timeout for these bits

    var newEnd;
    var inst = ev.data.instance;

    if($(this).scrollTop() < inst.padTop - $(this).height() / 4) {
        newEnd = moment(inst.displayStart).add(inst.displayDays * 2 + inst.overlapDays, 'days');
        if(newEnd >= inst.absoluteEnd) {
            newEnd = inst.absoluteEnd;
        }

        inst.updateData(newEnd, 'up');
    }
    else if($(this).scrollTop() + $(this).innerHeight() == $(this)[0].scrollHeight) {
        newEnd = moment(inst.displayStart).subtract(1, 'days');
        if(newEnd > inst.absoluteStart) {
            inst.updateData(newEnd, 'down');
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
