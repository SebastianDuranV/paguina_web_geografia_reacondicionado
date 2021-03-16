from flask import Flask, redirect, render_template, url_for, request, flash, make_response, session
from consultor_sql import User, Category , db, Blog, News, Monitoring, Proyects, Maps
import forms
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'Mi_perro_se_llama_manjar'
db.create_all()

TipeClass = dict(
    User = User,
    Category = Category,
    Blog = Blog ,
    News = News ,
    Monitoring = Monitoring ,
    Maps =  Maps ,
    Proyects = Proyects
)

# Inicio
@app.route('/Index')
def index():
    try:
        if session['idUser']:
            user = User.query.filter_by(id=session['idUser'])
            return render_template('index_user.html', isSuper = 0)
            #if user.isSuperUser:
            #    return render_template('index_user.html', isSuper = 1)
            #return render_template('index_user.html', isSuper = 0)
    except:
        return render_template("index.html")

#Crear objetos
formsPostDic = dict(
    Blog = forms.FormBlog ,
    News = forms.FormNews ,
    Monitoring = forms.FormMonitoring ,
    Maps =  forms.FormWebMaps ,
    Proyects = forms.FormProyects
)

translateNameSingle = dict(
    Blog = "Blog",
    News = "Noticias",
    Monitoring = "Monitoreo",
    Maps = "WebMaps",
    Proyects = "Proyectos"
)

# Cargar archivos en directorio ::::::::::::::::::
#Crear directorio
def createDirectory(id,type):
    directory = os.path.join('./proyecto-Geograf-a/static/uploaders/' + type, str(id))
    try:
        os.makedirs(directory)
    except:
        return "no se pudo crear archivo " + directory

#Cargar archivos
def upload(id,type,request):
    createDirectory(id,type)
    app.config['UPLOAD_FOLDER'] = "./proyecto-Geograf-a/static/uploaders/" + type +'/'+ str(id)
    #f = request.files['files']
    #filename = secure_filename(f.filename)
    #f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # save each "charts" file
    for file in request.files.getlist('charts'):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.name)))


@app.route('/createUser', methods = ['POST','GET'] )
def createUser():
    comment_form = forms.FormUser(request.form)
    if request.method == 'POST' and comment_form.validate():
        userName = comment_form.name.data
        lastname = comment_form.lastname.data
        password = comment_form.password.data
        email = comment_form.email.data
        user = User(username=userName , email=email, lastname = lastname, password=password )
        db.session.add(user)
        db.session.commit()
        flash("Usuario creado")
        return redirect(url_for('index'))
    else:
        return render_template('create_user.html', user=comment_form)

@app.route('/createCategory', methods = ['POST','GET'] )
def createCategory():
    comment_form = forms.FormCategory(request.form)
    if request.method == 'POST' and comment_form.validate():
        name = comment_form.name.data
        cat = Category(name=name)
        db.session.add(cat)
        db.session.commit()
        flash("Categoría para blog creado")
        return redirect(url_for('createCategory'))
    else:
         return render_template('create_category.html', cat=comment_form)

@app.route('/createPost/<type>', methods = ['POST','GET'] )
def createPost(type):
    comment_form = formsPostDic[type](request.form)
    if request.method == 'POST' and comment_form.validate():
        title = comment_form.title.data
        subtitle = comment_form.subtitle.data
        image = comment_form.image.data
        body = request.form['Article']
        user = User.query.filter_by(id= session['idUser']).first_or_404()
        if type == "Blog":
            category =  request.form.get('category')
            post = TipeClass[type](title=title, subtitle=subtitle, body=body,category=category, user=user, image=image)
        else:
            post = TipeClass[type](title=title, subtitle=subtitle, body=body, user=user, image=image)
        db.session.add(post)
        db.session.commit()
        post = TipeClass[type].query.filter_by(title=title, subtitle=subtitle, body=body, user=user).first_or_404()
        if request.files["files"]:
            upload(post.id,type,request)
        return render_template('create_post.html', type=translateNameSingle[type], post=comment_form, typeEng=type)
    else:
        if type == "Blog":
            cat = Category.query.all()
            return render_template('create_post.html', type=translateNameSingle[type], post=comment_form, typeEng=type, cat = cat)
        return render_template('create_post.html', type=translateNameSingle[type], post=comment_form, typeEng=type)




# Eliminar
@app.route('/deleteUser/<username>')
def delete_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/deleteCategory/<idCat>')
def delete_category(idCat):
    cat = Category.query.filter_by(id=idCat).first_or_404()
    db.session.delete(cat)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/deletePost/<type>/<idPost>')
def delete_post(idPost,type):
    post = TipeClass[type].query.filter_by(id=idPost).first_or_404()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))




#@app.route('/updateUser/<username>', methods = ['POST','GET'] )
#def updateUser(username):
#    user = User.query.filter_by(username=username).first_or_404()
#    if request.method == 'POST':
#        user.userName = request.form['username']
#        user.email = request.form['email']
#        db.session.commit()
#        flash("Usuario fue actualizado")
        #return redirect(url_for('index'))
#        return render_template('update_user.html' , user=user, username=username)
#    else:
#        return render_template('update_user.html' , user=user, username=username)


@app.route('/updateUserPerfil', methods = ['POST','GET'] )
def updatePerfil():
    id = session['idUser']
    user = User.query.filter_by(id=id).first_or_404()
    if request.method == 'POST':
        user.userName = request.form['username']
        user.lastName = request.form['lastname']
        user.email = request.form['email']
        user.password = request.form['password']
        db.session.commit()
        flash("Usuario fue actualizado")
        return render_template('update_user.html' , user=user)
    else:
        return render_template('update_user.html' , user=user)


@app.route('/updateCategory/<idCat>', methods = ['POST','GET'] )
def updateCategory(idCat):
    cat = Category.query.filter_by(id=idCat).first_or_404()
    if request.method == 'POST':
        cat.name = request.form['name']
        db.session.commit()
        flash("Categoría fue actualizado")
        return render_template('update_category.html', cat=cat, id=idCat)
    else:
        return render_template('update_category.html', cat=cat, id=idCat)

@app.route('/updatePost/<type>/<idPost>', methods = ['POST','GET'] )
def updatePost(idPost,type):
    post = TipeClass[type].query.filter_by(id=idPost).first_or_404()
    if request.method == 'POST':
        post.title = request.form['title']
        post.subtitle = request.form['subtitle']
        post.body = request.form['body']
        post.image = request.form['image']
        if type=='Blog':
            post.category_id = request.form['idcategory']
        db.session.commit()
        flash("Actualizado")
        return render_template('update_post.html', post=post, id=idPost, type=type)
    else:
        return render_template('update_post.html', post=post, id=idPost, type=type)


# Mostrar
@app.route('/getList')
def getList():
    getObject = request.args.get('type','<h1> No type declarated </h1>')
    try:
        user = User.query.filter_by(id=session['idUser'])
        allObject = TipeClass[getObject].query.filter_by(user_id=session['idUser'])
        #if user.isSuperUser == 0:
        #    allObject = TipeClass[getObject].query.filter_by(user_id=session['idUser'])
        #else:
        #    allObject = TipeClass[getObject].query.all()
    except:
        return '<h1> No found type </h1>'

    #user = User.query.filter_by(id=session['idUser'])
    #if user.isSuperUser:
    #    allObject = TipeClass[getObject].query.filter_by(User=user)
    #else:
    #    allObject = TipeClass[getObject].query.all()

    return render_template('show_list_types.html', objects=allObject , type=getObject)


@app.route('/user/<username>')
def show_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('show_user.html', user=user)


@app.route('/post/<type>/<idpost>')
def show_post(idpost,type):
    post = TipeClass[type].query.filter_by(id=idpost).first_or_404()
    otherpost = TipeClass[type].query.order_by(TipeClass[type].pub_date).all()

    # hacer un sistema de previo y siguiente
    for i in otherpost:
        print(i.id)
    return render_template('/Frontal/single.html', post=post)



# Sesiones de usuario
# ::: Entrar
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = forms.FormLoginUser(request.form)
    if request.method == 'POST' and login_form.validate():
        try:
            user = User.query.filter_by(email=login_form.email.data).first_or_404()
        except:
            flash("Email o contraseña no valida")
            return render_template('login.html', user = login_form)
        if login_form.password.data == user.password:
            session['idUser'] = user.id
            return redirect(url_for('index')) 
        else:
            flash("Email o contraseña no valida")
            return render_template('login.html', user = login_form)
    else:
        return render_template('login.html', user = login_form)

# ::: Salir
@app.route('/logout')
def logout():
    if 'idUser' in session:
        session.pop('idUser')
    return redirect(url_for('login'))




#### PAGINA NUEVA :::::::::
@app.route('/')
def indexx():
    blogs = Blog.query.all()
    news = News.query.all()
    proyects = Proyects.query.all()
    maps = Maps.query.all()
    monitoring = Monitoring.query.all()
    return render_template('/Frontal/index.html', blogs = blogs , news =news , proyects=proyects, monitoring= monitoring, maps = maps)


@app.route('/<type>')
def getPublicList(type):
    try:
        allObject = TipeClass[type].query.order_by(TipeClass[type].pub_date).all()
    except:
        return '<h1> No found type </h1>'
    if type == 'Blog':
        category = Category.query.all()
        return render_template('Frontal/list.html', posts = allObject , type='Blog', transType = 'Blog', category=category)
    return render_template('Frontal/list.html', posts = allObject , type=type, transType = translateNameSingle[type])

@app.route('/Blog/<idcategory>')
def getPublicListBlogCategory(idcategory):
    category = Category.query.filter_by(id=idcategory).all()
    allObject = TipeClass[type].query.filter_by(category=category).all()
    return render_template('Frontal/list.html', posts = allObject , type='Blog', transType = 'Blog', category=category)

@app.route('/contact_us')
def contact_us():
    return render_template('/Frontal/contact_us.html')  

@app.route('/single')
def single():
    return render_template('/Frontal/single.html')

#@app.route('/c')
#def c():
#    return render_template('/Frontal/carusel.html')




#if __name__=='__main__':
#    app.run(host= '0.0.0.0',debug=True)



