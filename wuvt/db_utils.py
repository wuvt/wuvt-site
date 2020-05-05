from wuvt import db
from wuvt.models import Page
from wuvt.auth.models import User
from wuvt.blog.models import Article, Category


def initdb(username, password):
    db.create_all()

    cats = [Category("Events", "events", True),
            Category("Music Adds", "music-adds", True),
            Category("Programming", "programming", True),
            Category("Updates", "station-updates", True),
            Category("Woove", "woove", True)]
    for cat in cats:
        db.session.add(cat)

    # Create the first account
    user = User(str(username), str(username),
                "{0}@localhost".format(username))
    user.set_password(str(password))
    db.session.add(user)


def add_sample_data():
    add_sample_articles()
    add_sample_pages()


def add_sample_articles():
    article = Article("Cloud Nothings Prize Pack Giveaway",
                      'cloud-nothings-prize-pack-giveaway', 1, 1, """\
![I dont even know what this is](/static/img/article_pic.png)

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce ut posuere
nulla. Ut varius, turpis at euismod ullamcorper, turpis libero sollicitudin
lectus, vitae pellentesque magna nibh vel arcu. Etiam non euismod velit. Sed
sit amet risus tempus, viverra mauris in, consectetur dui. Morbi purus nunc,
mollis quis sapien et, posuere vehicula metus. Ut leo erat, blandit non urna
vitae, finibus tempor augue. Class aptent taciti sociosqu ad litora torquent
per conubia nostra, per inceptos himenaeos.

Curabitur sagittis metus ac consequat porttitor. Donec vitae augue sed erat
pulvinar cursus a quis odio. Maecenas vehicula augue volutpat augue laoreet
porttitor. Mauris eget bibendum neque, nec efficitur lorem. Vestibulum
ultrices, urna quis sollicitudin accumsan, risus sapien aliquet mi, nec porta
justo turpis in massa. Mauris arcu erat, sollicitudin ac feugiat quis, finibus
nec lorem. Fusce a metus orci. Orci varius natoque penatibus et magnis dis
parturient montes, nascetur ridiculus mus. Vivamus at pharetra enim. Fusce ac
commodo magna, at imperdiet tellus. Praesent dapibus erat justo, vel
pellentesque tellus vehicula at. In hac habitasse platea dictumst.

Integer eget commodo diam, at lacinia odio. Duis consequat condimentum mauris
quis vestibulum. Quisque ac lobortis magna, sit amet rutrum nisi. Curabitur
dapibus nisl ut nibh semper placerat. Praesent pharetra, arcu et commodo
vehicula, nunc mauris semper diam, vitae accumsan urna quam id ante. Maecenas
maximus, elit vitae feugiat lacinia, orci nibh porttitor augue, at tincidunt
felis magna nec odio. Cras et mi vel dui vulputate rhoncus a eu mi. Proin elit
dui, facilisis in risus eu, aliquam suscipit libero. Sed vitae nibh mauris. Ut
placerat efficitur congue. Aliquam quis magna vehicula, lacinia justo vitae,
mollis tellus. Aliquam at nibh nec metus auctor viverra. Donec fermentum, leo
non fermentum fringilla, tortor tellus cursus magna, ac dignissim ipsum dolor
tempus nulla.

Duis eget ipsum ultricies, condimentum nunc vel, gravida metus. Curabitur porta
purus felis, vel tempor ex feugiat nec. Nulla quam augue, porttitor id leo at,
vestibulum viverra urna. Integer sagittis ex eu tellus vulputate lacinia. Donec
porta eu ligula rhoncus vulputate. Fusce finibus erat ac elit congue, at
scelerisque lorem porttitor. Vivamus magna dolor, gravida a est et, interdum
sodales sapien. Pellentesque a ultricies massa. Phasellus a dictum sapien.

Mauris dictum rutrum purus, eu ullamcorper ipsum tempor at. Integer egestas
volutpat leo, non faucibus felis venenatis eget. Curabitur a iaculis lectus.
Quisque sagittis tempus felis a consequat. Nullam dui sem, cursus in convallis
sed, placerat vel velit. Nulla pellentesque libero sed tortor ullamcorper
dapibus nec sed nunc. Sed vel neque tempus, dapibus turpis a, dignissim neque.
Cras iaculis nibh eros, nec iaculis purus viverra non.
""", published=True)
    article.front_page = True
    db.session.add(article)
    article.render_html()
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

    article = Article("Hudson Hits Another Buzzer Beater in Hokies Win",
                      'hudson-hits-another-buzzer-beater-in-hokies-win', 1, 1,
                      """\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi sed blandit
felis. Suspendisse massa tellus, congue volutpat sapien eu, imperdiet commodo
massa. Donec quis gravida mi. Suspendisse tempor ligula mauris, non consequat
diam auctor id. Nullam mattis sed urna vitae vestibulum. Donec eros mi,
placerat congue dolor vel, accumsan aliquet orci. Suspendisse potenti. Donec
nec sollicitudin leo, id vulputate ipsum. In pellentesque maximus sapien, sit
amet viverra lorem sollicitudin ut. Phasellus tincidunt ultricies sapien in
tincidunt.

Integer justo metus, dictum et imperdiet sed, mollis ultricies libero. Sed
eleifend ut quam eget ullamcorper. Pellentesque ipsum sem, cursus vitae massa
quis, condimentum rutrum mauris. Donec ornare pretium nunc vitae pretium. Class
aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos
himenaeos. In in tristique felis, non ornare nisl. Ut suscipit sem nec ante
mollis, a vehicula nisl finibus. Mauris nec risus blandit, bibendum diam in,
porta leo. Proin rutrum risus eu mollis dapibus.

## Lorem ipsum
Interdum et malesuada fames ac ante ipsum primis in faucibus. Phasellus ac ante
ac turpis lacinia molestie a sed quam. Proin condimentum ut massa in lobortis.
Quisque et finibus dolor. Sed pharetra sodales congue. Pellentesque ullamcorper
molestie finibus. Curabitur cursus mi ac odio hendrerit, ac venenatis quam
molestie.

Maecenas ante nisi, tincidunt nec molestie ut, dictum et dui. Cras vestibulum
ipsum sed semper cursus. Sed vulputate sit amet neque nec lacinia. Cras sit
amet nunc sagittis nisi faucibus hendrerit. In ex urna, gravida vel nisl a,
cursus vestibulum erat. Suspendisse orci dui, elementum in dolor ut, feugiat
scelerisque eros. Nullam malesuada nulla at porta convallis. Proin gravida
libero eu ultricies viverra. Nulla accumsan, metus a mattis malesuada, enim
libero lacinia tellus, vel commodo ipsum turpis eget sem. Donec ac augue non
felis euismod iaculis. Vivamus fringilla rutrum magna eget viverra. Etiam vitae
velit nunc. Integer semper venenatis pharetra. Integer ullamcorper justo elit,
non pulvinar libero tristique a. Nam vel efficitur urna.

Quisque leo ex, fermentum at volutpat eu, venenatis condimentum leo. Quisque
faucibus odio sed elit sodales, at sagittis lectus iaculis. Suspendisse
vestibulum maximus justo, id vulputate ante. Morbi rutrum sollicitudin augue
eget hendrerit. Cras lacinia, purus a pulvinar consectetur, velit sem
condimentum massa, id faucibus risus orci eget quam. Nulla efficitur pulvinar
metus nec luctus. Curabitur dolor ipsum, blandit ac ex nec, ultricies egestas
orci. Sed tempor facilisis enim, in vehicula velit ornare a. Quisque non metus
odio.
""", published=True)
    article.front_page = True
    db.session.add(article)
    article.render_html()
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise


def add_sample_pages():
    db.session.add(Page("Stream", "listen-live", """\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras nunc sem, auctor blandit augue ac, suscipit mollis ligula. Phasellus pulvinar placerat nibh, non ultrices diam consectetur sed. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis non tellus purus. Suspendisse potenti. Donec rhoncus blandit nunc, id sollicitudin dui posuere non. Sed placerat pretium justo, sit amet congue augue viverra vitae. Sed porta sem vel egestas vestibulum. Praesent id finibus sem, eu cursus libero. In hac habitasse platea dictumst. Suspendisse tristique est sed libero fermentum vestibulum. Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Phasellus mi nisl, efficitur sed lobortis sed, porta at tellus. Fusce varius vestibulum erat in rhoncus. Praesent ac neque eget eros elementum feugiat. Cras vitae nisl tempor lectus dictum dignissim eu at purus. Vestibulum sodales tincidunt egestas. Integer luctus lorem orci, ut placerat leo fermentum in. Pellentesque lacinia, diam at facilisis semper, lorem nibh pharetra dolor, eleifend pharetra elit dolor vel urna. Nulla scelerisque lectus in justo scelerisque eleifend. Etiam et nisi ut lorem aliquam fringilla.

Curabitur sit amet dui dignissim, ornare ligula sit amet, fringilla tellus. Sed sed elementum felis. Aliquam feugiat mi nec lacus faucibus bibendum. Phasellus sit amet urna eget dolor laoreet sodales. Phasellus id ullamcorper felis. Praesent vel cursus elit. Interdum et malesuada fames ac ante ipsum primis in faucibus.

Nunc sed purus vitae urna bibendum eleifend eu ac quam. Cras aliquam aliquam tortor, a ornare ligula tristique a. Cras convallis scelerisque quam ut accumsan. Fusce ut iaculis mi. Ut vulputate enim quis diam dignissim iaculis. Vivamus fringilla purus vel neque tincidunt, accumsan aliquet justo porttitor. Cras vel nulla tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.

Proin vel lorem pretium, tempus velit et, sagittis tortor. Integer hendrerit massa a neque feugiat, eget semper nisi rhoncus. Mauris non nisl vitae dui varius vehicula a sed dolor. Morbi dignissim viverra vestibulum. Curabitur a egestas tellus. Curabitur vitae commodo ligula, eu sodales elit. Praesent malesuada turpis nec elit malesuada, vitae tempor est vestibulum. Vestibulum nisl erat, finibus semper egestas a, ultrices eu lorem.
""", True, "about"))
    db.session.add(Page("Donate", "donate", """\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus rutrum sit amet libero in tempus. Duis lacinia, massa sit amet fermentum euismod, ante elit tincidunt augue, ac ultrices enim risus a urna. Curabitur finibus risus ante, eu pharetra lorem consequat nec. Etiam id eros ac diam ultrices imperdiet. Praesent suscipit, purus finibus maximus aliquet, lectus dolor fermentum nulla, non tempus velit eros sed metus. Nunc ut mollis enim, a rutrum turpis. Aliquam quis tincidunt velit, vitae accumsan neque. Phasellus ut eleifend lectus. Curabitur non quam massa. In lacinia suscipit velit, sed ultricies justo bibendum accumsan. Integer cursus ex quam, vitae maximus orci pharetra sit amet.

Integer interdum risus vestibulum lacus rutrum, vitae efficitur quam lobortis. Donec pretium tellus eu ligula rutrum tristique. Vestibulum ultrices metus leo, in rhoncus nisl consectetur id. Curabitur sit amet pellentesque ante, eget fermentum nulla. Sed egestas aliquam neque, eget porttitor velit varius ut. Nam magna massa, tincidunt in est sed, imperdiet congue massa. Curabitur sem purus, pulvinar a pellentesque vel, vehicula vitae metus. Curabitur egestas sit amet mauris vel vulputate. Quisque maximus, odio vitae fringilla euismod, nibh neque sollicitudin enim, eu porttitor quam sapien id urna. Quisque interdum tortor feugiat lobortis tempus. Aliquam erat volutpat.

Fusce tempor pretium mattis. Curabitur congue erat et lorem consectetur tristique eget vel lectus. Phasellus sagittis vehicula faucibus. Ut cursus et diam ac finibus. Curabitur facilisis odio vitae ante sagittis, et maximus lorem commodo. Ut ac justo quis nunc faucibus euismod volutpat non lorem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi efficitur vitae arcu sed finibus. Nam vel odio erat. Duis at aliquet mauris. Donec vulputate massa at imperdiet imperdiet. Nam fringilla tempus lacus non congue. Etiam a nibh nibh. Aenean molestie, tortor quis faucibus fringilla, sapien massa aliquam magna, id dictum libero mi at quam. Integer maximus at lorem id commodo.

Nam feugiat porta commodo. Vestibulum tellus arcu, sollicitudin luctus vulputate in, pretium et erat. Maecenas tellus erat, scelerisque non ultricies ut, sagittis id lacus. Ut et aliquet justo. Donec sed aliquet ex. Cras hendrerit, libero a mollis hendrerit, risus metus laoreet urna, porta ornare diam nibh condimentum risus. Curabitur eget lacinia velit.

Mauris egestas lectus dolor. Donec non augue id tellus volutpat ultricies. Sed consectetur magna semper tincidunt bibendum. Cras eget tempus orci. Cras pharetra ex in mauris placerat, vitae facilisis nisl egestas. Sed molestie ex mollis dolor congue posuere. Nulla sagittis lacinia tempus. Nulla et vestibulum diam. Cras id molestie metus. Aenean condimentum tellus sapien, at aliquam dui consequat vel. Cras posuere ultrices lectus. Quisque placerat velit lorem, volutpat rhoncus turpis sodales ac. Sed viverra mi elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
""", True, "contact"))
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise
