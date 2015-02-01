#!/usr/bin/env python2

from wuvt import db
from wuvt.blog.models import Article

article = Article("Cloud Nothings Prize Pack Giveaway",
    'cloud-nothings-prize-pack-giveaway', 1, 1, """\

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
db.session.add(article)
article.render_html()
db.session.commit()

article = Article("Hudson Hits Another Buzzer Beater in Hokies Win",
    'hudson-hits-another-buzzer-beater-in-hokies-win', 1, 2, """\
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
db.session.add(article)
article.render_html()
db.session.commit()
