// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

function PlaylistsByDate(wrapper) {
    // number of days to display each time we scroll
    this.displayDays = 10;

    // we subtract these so the current day is really the last overlap day
    this.absoluteEnd = moment().endOf('day');

    // start date for playlists by date viewer
    //this.absoluteStart = moment("2007-09-07");
    this.absoluteStart = moment("2015-03-05");

    this.loading = false;
    this.wrapper = wrapper;

    // create content divs
    this.cdiv1 = document.createElement('div');
    $(this.wrapper).append(this.cdiv1);
    this.cdiv2 = document.createElement('div');
    $(this.wrapper).append(this.cdiv2);
    this.cdiv3 = document.createElement('div');
    $(this.wrapper).append(this.cdiv3);
}

PlaylistsByDate.prototype.loadDateSet = function(dateToLoad, destDiv, direction) {
    direction = typeof direction !== 'undefined' ? direction : null;

    this.loading = true;
    this.topReached = false;
    this.bottomReached = false;
    var inst = this;
    var start = moment(dateToLoad).subtract(this.displayDays, 'days');

    if(direction == 'up' && dateToLoad > this.absoluteEnd) {
        this.topReached = true;
    }
    else if(direction == 'down' && start < this.absoluteStart) {
        this.bottomReached = true;
    }

    $.ajax({
        'url': '/playlists/date/data?start=' + start.toISOString() + '&end=' + dateToLoad.toISOString(),
        'dataType': 'json',
    }).done(function(data) {
        var sets = data['sets'];
        var days = {};
        var daysLoaded = 0;

        for(i in sets) {
            var key = moment(sets[i]['dtstart']).startOf('day');
            if(key in days) {
                days[key].push(sets[i]);
            }
            else {
                days[key] = [sets[i]];
                daysLoaded++;
            }
        }

        // remove existing data
        $(destDiv).html('');

        for(date in days) {
            var head = document.createElement('header');
            $(head).text(moment(date).format('dddd, MMMM D, YYYY'));

            var list = document.createElement('ul');
            $.each(days[date], function(index, value) {
                var link = document.createElement('a');
                link.href = '/playlists/set/' + value['id'];

                if(value['dtend'] != null) {
                    $(link).text(moment(value['dtstart']).format('HH:mm') + "-" + moment(value['dtend']).format('HH:mm') + ": " + value['dj']['airname']);
                }
                else {
                    $(link).text(moment(value['dtstart']).format('HH:mm') + "-: " + value['dj']['airname']);
                }

                makeAjaxLink(link);

                var li = document.createElement('li');
                $(li).append(link);
                $(list).append(li);
            });

            var section = document.createElement('section');
            $(section).append(head);
            $(section).append(list);
            $(destDiv).append(section);
        }

        if(direction == 'up' || direction == 'jump') {
            $(inst.wrapper).scrollTop($(inst.cdiv2).position().top);
        }

        inst.loading = false;
    });
}

PlaylistsByDate.prototype.jumpToDate = function(dt) {
    if(dt < this.absoluteStart) {
        dt = this.absoluteStart;
    }
    else if(dt > this.absoluteEnd) {
        dt = this.absoluteEnd;
    }

    this.activeDate = moment(dt).endOf('day');

    this.loadDateSet(
        moment(this.activeDate).add(this.displayDays, 'days'), this.cdiv1);
    this.loadDateSet(this.activeDate, this.cdiv2, 'jump');
    this.loadDateSet(
        moment(this.activeDate).subtract(this.displayDays, 'days'), this.cdiv3);
}

PlaylistsByDate.prototype.scrollUp = function() {
    if(this.topReached) {
        return;
    }

    $(this.cdiv3).remove();
    this.cdiv3 = this.cdiv2;
    this.cdiv2 = this.cdiv1;

    this.cdiv1 = document.createElement('div');
    $(this.wrapper).prepend(this.cdiv1);

    // activeDate business
    this.activeDate = moment(this.activeDate).add(this.displayDays, 'days');
    this.loadDateSet(
        moment(this.activeDate).add(this.displayDays, 'days'),
        this.cdiv1, 'up');
}

PlaylistsByDate.prototype.scrollDown = function() {
    if(this.bottomReached) {
        return;
    }

    $(this.cdiv1).remove();
    this.cdiv1 = this.cdiv2;
    this.cdiv2 = this.cdiv3;

    this.cdiv3 = document.createElement('div');
    $(this.wrapper).append(this.cdiv3);

    // activeDate business
    this.activeDate = moment(this.activeDate).subtract(
        this.displayDays, 'days');
    this.loadDateSet(
        moment(this.activeDate).subtract(this.displayDays, 'days'),
        this.cdiv3, 'down');
}

PlaylistsByDate.prototype.handleScroll = function(ev) {
    var newEnd;
    var inst = ev.data.instance;

    // TODO: add a timeout for these bits

    if(!$(this).is(':animated') && !inst.loading) {
        if($(this).scrollTop() <= $(this.cdiv1).height()) {
            inst.scrollUp();
        }
        else if($(this).scrollTop() + $(this).innerHeight() >= $(this)[0].scrollHeight) {
            inst.scrollDown();
        }
    }
}

PlaylistsByDate.prototype.init = function() {
    $(this.wrapper).bind('scroll', {'instance': this}, this.handleScroll);
    $('#date_jump_form').bind('submit', {'instance': this}, function(ev) {
        ev.data.instance.jumpToDate(moment($('#date_entry').val()));
        return false;
    });

    this.jumpToDate(this.absoluteEnd);
}

// @license-end
