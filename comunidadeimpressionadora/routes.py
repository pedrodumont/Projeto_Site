from flask import render_template, redirect, flash, url_for, request, abort
from comunidadeimpressionadora import app, database, bcrypt
from comunidadeimpressionadora.forms import FormCriarConta, FormLogin, FormEditarPerfil, FormCriarPost
from comunidadeimpressionadora.models import Usuario, Post
from flask_login import login_user, logout_user, current_user, login_required
import arrow, pytz
import secrets
import os
from PIL import Image

def formata_data(data_criacao):
    timezone_local = pytz.timezone('America/Sao_Paulo')
    data_local = arrow.get(data_criacao).to(timezone_local)
    return data_local.strftime('%d %b %Y, %H:%M'), data_local.humanize()

@app.route('/')
def home():
    posts = Post.query.order_by(Post.id.desc())
    return render_template('home.html', posts=posts, formata_data=formata_data)

@app.route('/contato')
def contato():
    return render_template('contato.html')


@app.route('/usuarios')
@login_required
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', lista_usuarios=lista_usuarios)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    form_criarconta = FormCriarConta()
    
    if form_login.validate_on_submit() and 'botao_login' in request.form: 
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            login_user(usuario, remember=form_login.lembrar_dados.data)
            flash(f'Login feito com sucesso no e-mail: {form_login.email.data}', 'alert-success')
            par_next = request.args.get('next')
            if par_next:
                return redirect(par_next)
            return redirect(url_for('home'))
        else:
            flash(f'Falha no login. E-mail ou Senha incorretos', 'alert-danger')
            
    if form_criarconta.validate_on_submit() and 'botao_criarconta' in request.form:
        senha_crypt = bcrypt.generate_password_hash(form_criarconta.senha.data)
        usuario = Usuario(username=form_criarconta.username.data, 
                        email=form_criarconta.email.data, 
                        senha=senha_crypt)
        database.session.add(usuario)
        database.session.commit()
        flash(f'Conta criada com sucesso no e-mail: {form_criarconta.email.data}', 'alert-success')
        return redirect(url_for('home'))
    return render_template('login.html', form_login=form_login, form_criarconta=form_criarconta)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(f'Logout feito com sucesso.', 'alert-success')
    return redirect(url_for('home'))

@app.route('/perfil')
@login_required
def perfil():
    foto_perfil = url_for('static', filename = f'fotos_perfil/{current_user.foto_perfil}')
    return render_template('perfil.html', foto_perfil=foto_perfil)

@app.route('/post/criar', methods=['GET', 'POST'])
@login_required
def criar_post():
    form = FormCriarPost()
    if form.validate_on_submit():
        post = Post(titulo=form.titulo.data, corpo=form.corpo.data, autor=current_user)
        database.session.add(post)
        database.session.commit()
        flash('Postagem criada com Sucesso', 'alert-success')
        return redirect(url_for('home'))
        
    return render_template('criarpost.html', form=form)

def salvar_imagem(imagem):
    codigo = secrets.token_hex(8)
    nome, extensao = os.path.splitext(imagem.filename)
    nome_arquivo = nome + codigo + extensao
    caminho_completo = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)
    tamanho_img = (200,200)
    imagem_reduzida = Image.open(imagem)
    imagem_reduzida.thumbnail(tamanho_img)
    imagem_reduzida.save(caminho_completo)
    
    return nome_arquivo

def atualizar_cursos(form):
    lista_cursos = []
    
    for curso in form:
        if 'curso_' in curso.name:
            if curso.data:
                lista_cursos.append(curso.label.text)
            
    return ';'.join(lista_cursos)

@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = FormEditarPerfil()
    foto_perfil = url_for('static', filename = f'fotos_perfil/{current_user.foto_perfil}')
    
    if form.validate_on_submit():
        # atualizar username e email
        current_user.email = form.email.data
        current_user.username = form.username.data
        
        # atualizar foto de perfil
        if form.foto_perfil.data:
            imagem = salvar_imagem(form.foto_perfil.data)
            current_user.foto_perfil = imagem
            
        #atualizar cursos    
        current_user.cursos = atualizar_cursos(form)
        
        #salvar no banco
        database.session.commit()
        flash('Perfil atualizado com Sucesso', 'alert-success')
        
        return redirect(url_for('perfil'))
    
    elif request.method == 'GET':
        form.email.data = current_user.email
        form.username.data = current_user.username
    
    return render_template('editarperfil.html', foto_perfil=foto_perfil, form=form )

@app.route('/post/<post_id>', methods=['GET', 'POST'])
def exibir_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        form = FormCriarPost()
        if request.method == 'GET':
            form.titulo.data = post.titulo
            form.corpo.data = post.corpo 
        elif form.validate_on_submit():
            post.titulo = form.titulo.data
            post.corpo = form.corpo.data
            database.session.commit()
            flash('Post Atualizado com Sucesso!', 'alert-success')
            return redirect(url_for('home'))
    else:
        form = None
        
    return render_template('post.html', post=post, form=form, formata_data=formata_data)

@app.route('/post/<post_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        database.session.delete(post)
        database.session.commit()
        flash('Post excluido com Sucesso!', 'alert-danger')
        return redirect(url_for('home'))
    else:
        abort(403)