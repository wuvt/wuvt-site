from wuvt import db
from wuvt.blog.models import Article
from wuvt.trackman.models import DJ, Track
from wuvt.models import Page


def add_sample_articles():
    article = Article(u"Cloud Nothings Prize Pack Giveaway",
                      u'cloud-nothings-prize-pack-giveaway', 1, 1, u"""\
![I dont even know what this is](/static/img/article_pic.png)

Yolo ipsum ratione commodi repellendus minus and so I did, but that was last
month quidem. Illo enim libero aperiam impedit distinctio aliquid. Praesentium
incidunt sunt asperiores magni dealing with a heart that I didn't break
blanditiis. Voluptatum dolore aut nulla quidem and I wish she wasn't married.

Odit rest in peace mac dre, I'mma do it for the bay, okay accusamus alias
illo hic minima. Cupiditate atque nam sit quae ducimus quia sint. Qui what you
bothering me for? dignissimos hell yeah, hell yeah qui libero If you hurt, I
don't tell you. Provident distinctio nostrum soluta accusantium voluptates.

## Yolo ipsum
Cupiditate iste beatae fuckin' right, all right ipsam sint. Non dolorem
blanditiis facere neque excepturi amet. Id illo non officia placeat velit
distinctio. Vero perspiciatis animi qui quisquam eum.

Consequatur aut nemo est optio placeat. Ut illum at impedit ut repellat.
Quia est et nobis labore then right after texting I told her I'm faded damn
right, all right. Mollitia molestias quis one time, been in love one time
voluptatem aut maxime molestiae. Officia et qui I'm in the building and I'm
feeling myself I've had mine, you've had yours we both know quia cumque we all
have our nights though, don't be so ashamed.

Vero similique ab exercitationem ipsam blanditiis vitae vitae. Quis aliquid
ea It's women to call ex voluptas aperiam. Incidunt consequatur culpa autem
listen, listen, whoa, yeah, listen, ooooh consequuntur ut quis. We all have our
nights though, don't be so ashamed impedit ab officiis autem odit you hate the
fact that you bought the dream.
""", published=True)
    article.front_page = True
    db.session.add(article)
    article.render_html()
    db.session.commit()

    article = Article(u"Hudson Hits Another Buzzer Beater in Hokies Win",
                      u'hudson-hits-another-buzzer-beater-in-hokies-win', 1, 1,
                      u"""\
Yolo ipsum rerum est delectus cumque aliquam quia aliquid. I'm fucked up,
torn down officiis accusamus repudiandae harum sint quas. Suscipit eligendi
quasi vel veritatis enim est. Tenetur autem consequuntur sint aut soluta nostrum.

Nesciunt laboriosam voluptas repellat nemo repellendus aut. One time, been
in love one time quo I keep thinking you just don't know corrupti quo numquam
recusandae. That she only see when she feels obligated quo recusandae nisi they
loving the crew enim aliquid aut. Ipsa quisquam doloribus accusamus explicabo
est voluptatem.

Dignissimos quam omnis in autem id excepturi. Possimus molestiae fuga tell
uncle luke I'm out in miami too fugiat obcaecati ipsam. Blanditiis non we eat
each other whenever we at the dinner table et voluptatum possimus. If you let
me, here's what I'll do error obcaecati It's cause we blowing like a c4 ut
autem suscipit. Ipsam nostrum inventore unde est culpa est voluptas.

Libero they loving the crew laudantium minima ut possimus soluta. Enim autem
et atque nulla like we sittin' on the bench, nigga we don't really play quae
(and we say) hell yeah. Est aperiam quo quisquam quis eos et. Id minima iusto
voluptas laborum sequi quia et. Aliquid facilis a laudantium the realest niggas
say 'your lyrics do shit for me' et sit ad.

Qui I've loved and I've lost quae ipsa id even though it's fucked up, girl,
I'm still fucking wit ya quis. Odit voluptate energizer bunny omnis vero
numquam est. Quia placeat go uptown, new york city biiitch oh, they lovin the
crew but my mind didn't change you won't ever have to hide qui.
""", published=True)
    article.front_page = True
    db.session.add(article)
    article.render_html()
    db.session.commit()


def add_sample_pages():
    db.session.add(Page(u"Stream", u"listen-live", u"""\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras nunc sem, auctor blandit augue ac, suscipit mollis ligula. Phasellus pulvinar placerat nibh, non ultrices diam consectetur sed. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis non tellus purus. Suspendisse potenti. Donec rhoncus blandit nunc, id sollicitudin dui posuere non. Sed placerat pretium justo, sit amet congue augue viverra vitae. Sed porta sem vel egestas vestibulum. Praesent id finibus sem, eu cursus libero. In hac habitasse platea dictumst. Suspendisse tristique est sed libero fermentum vestibulum. Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Phasellus mi nisl, efficitur sed lobortis sed, porta at tellus. Fusce varius vestibulum erat in rhoncus. Praesent ac neque eget eros elementum feugiat. Cras vitae nisl tempor lectus dictum dignissim eu at purus. Vestibulum sodales tincidunt egestas. Integer luctus lorem orci, ut placerat leo fermentum in. Pellentesque lacinia, diam at facilisis semper, lorem nibh pharetra dolor, eleifend pharetra elit dolor vel urna. Nulla scelerisque lectus in justo scelerisque eleifend. Etiam et nisi ut lorem aliquam fringilla.

Curabitur sit amet dui dignissim, ornare ligula sit amet, fringilla tellus. Sed sed elementum felis. Aliquam feugiat mi nec lacus faucibus bibendum. Phasellus sit amet urna eget dolor laoreet sodales. Phasellus id ullamcorper felis. Praesent vel cursus elit. Interdum et malesuada fames ac ante ipsum primis in faucibus.

Nunc sed purus vitae urna bibendum eleifend eu ac quam. Cras aliquam aliquam tortor, a ornare ligula tristique a. Cras convallis scelerisque quam ut accumsan. Fusce ut iaculis mi. Ut vulputate enim quis diam dignissim iaculis. Vivamus fringilla purus vel neque tincidunt, accumsan aliquet justo porttitor. Cras vel nulla tellus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.

Proin vel lorem pretium, tempus velit et, sagittis tortor. Integer hendrerit massa a neque feugiat, eget semper nisi rhoncus. Mauris non nisl vitae dui varius vehicula a sed dolor. Morbi dignissim viverra vestibulum. Curabitur a egestas tellus. Curabitur vitae commodo ligula, eu sodales elit. Praesent malesuada turpis nec elit malesuada, vitae tempor est vestibulum. Vestibulum nisl erat, finibus semper egestas a, ultrices eu lorem.
""", True, u"about"))
    db.session.add(Page(u"Donate", u"donate", u"""\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus rutrum sit amet libero in tempus. Duis lacinia, massa sit amet fermentum euismod, ante elit tincidunt augue, ac ultrices enim risus a urna. Curabitur finibus risus ante, eu pharetra lorem consequat nec. Etiam id eros ac diam ultrices imperdiet. Praesent suscipit, purus finibus maximus aliquet, lectus dolor fermentum nulla, non tempus velit eros sed metus. Nunc ut mollis enim, a rutrum turpis. Aliquam quis tincidunt velit, vitae accumsan neque. Phasellus ut eleifend lectus. Curabitur non quam massa. In lacinia suscipit velit, sed ultricies justo bibendum accumsan. Integer cursus ex quam, vitae maximus orci pharetra sit amet.

Integer interdum risus vestibulum lacus rutrum, vitae efficitur quam lobortis. Donec pretium tellus eu ligula rutrum tristique. Vestibulum ultrices metus leo, in rhoncus nisl consectetur id. Curabitur sit amet pellentesque ante, eget fermentum nulla. Sed egestas aliquam neque, eget porttitor velit varius ut. Nam magna massa, tincidunt in est sed, imperdiet congue massa. Curabitur sem purus, pulvinar a pellentesque vel, vehicula vitae metus. Curabitur egestas sit amet mauris vel vulputate. Quisque maximus, odio vitae fringilla euismod, nibh neque sollicitudin enim, eu porttitor quam sapien id urna. Quisque interdum tortor feugiat lobortis tempus. Aliquam erat volutpat.

Fusce tempor pretium mattis. Curabitur congue erat et lorem consectetur tristique eget vel lectus. Phasellus sagittis vehicula faucibus. Ut cursus et diam ac finibus. Curabitur facilisis odio vitae ante sagittis, et maximus lorem commodo. Ut ac justo quis nunc faucibus euismod volutpat non lorem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Morbi efficitur vitae arcu sed finibus. Nam vel odio erat. Duis at aliquet mauris. Donec vulputate massa at imperdiet imperdiet. Nam fringilla tempus lacus non congue. Etiam a nibh nibh. Aenean molestie, tortor quis faucibus fringilla, sapien massa aliquam magna, id dictum libero mi at quam. Integer maximus at lorem id commodo.

Nam feugiat porta commodo. Vestibulum tellus arcu, sollicitudin luctus vulputate in, pretium et erat. Maecenas tellus erat, scelerisque non ultricies ut, sagittis id lacus. Ut et aliquet justo. Donec sed aliquet ex. Cras hendrerit, libero a mollis hendrerit, risus metus laoreet urna, porta ornare diam nibh condimentum risus. Curabitur eget lacinia velit.

Mauris egestas lectus dolor. Donec non augue id tellus volutpat ultricies. Sed consectetur magna semper tincidunt bibendum. Cras eget tempus orci. Cras pharetra ex in mauris placerat, vitae facilisis nisl egestas. Sed molestie ex mollis dolor congue posuere. Nulla sagittis lacinia tempus. Nulla et vestibulum diam. Cras id molestie metus. Aenean condimentum tellus sapien, at aliquam dui consequat vel. Cras posuere ultrices lectus. Quisque placerat velit lorem, volutpat rhoncus turpis sodales ac. Sed viverra mi elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
""", True, u"contact"))
    db.session.commit()


def add_sample_djs():
    db.session.add(DJ(u'Testy McTesterson', u'Testy McTesterson'))
    db.session.commit()


def add_sample_tracks():
    db.session.add(Track(u'The Divine Conspiracy', u'Epica', u'The Divine Conspiracy', u'Avalon'))
    db.session.add(Track(u'Second Stone', u'Epica', u'The Quantum Enigma', u'Nuclear Blast'))
    db.session.commit()
