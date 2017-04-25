from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm,\
    CommentForm, EditCompanyProfileForm, ApplicantForm, TaskForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, Application, Task
from ..decorators import admin_required, permission_required


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, title=form.title.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/company_homepage')
def company_homepage():
    return render_template('companies_homepage.html')

@main.route('/student_homepage')
def student_homepage():
    return render_template('student_homepage.html')

@main.route('/team')
def team():
    return render_template('team.html')

@main.route('/apply/<int:id>', methods=['GET', 'POST'])
@login_required
def apply(id):
    post = Post.query.get_or_404(id)
    application = Application.query.filter_by(post_id=id, applicant_id=current_user.id).first()
    if current_user == post.author:
        abort(403)
    form = ApplicantForm()
    if form.validate_on_submit():
        if application:
            if not application.applicant_id == current_user.id:
                app_count = post.applicant_count
                app_count = int(app_count) + 1
                post.applicant_count = app_count
                app = Application(applicant_id=current_user.id,
                                  post_id=id)
                db.session.add(app)
                flash('Applied for this job')
                return redirect(url_for('.post', id=post.id))
            elif application.applicant_id == current_user.id:
                flash('You already applied for this job')
                return redirect(url_for('.post', id=post.id))
        else:
                app_count = post.applicant_count
                app_count = int(app_count) + 1
                post.applicant_count = app_count
                app = Application(applicant_id=current_user.id,
                                  post_id=id)
                db.session.add(app)
                flash('Applied for this job')
                return redirect(url_for('.post', id=post.id))
    return render_template('apply.html', posts=[post], form=form)

@main.route('/applicants/<int:id>', methods=['GET', 'POST'])
@login_required
def applicants(id):
    post = Post.query.get_or_404(id)
    apps = Application.query.filter_by(post_id=id)
    return render_template('applicants.html', post=
    post, apps=apps)

@main.route('/hired/<int:id>', methods=['GET', 'POST'])
@login_required
def hired(id):
    post = Post.query.get_or_404(id)
    apps = Application.query.filter_by(post_id=id, approved=True)
    tasks = Task.query.filter_by(post_id=id, done=False)
    form1 = CommentForm(prefix="form1")
    form2 = TaskForm(prefix="form2")
    if form1.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    if form2.validate_on_submit():
        for app in apps:
            task = Task(description=form2.body.data, post_id=id,
                              worker_id=app.applicant_id)
            db.session.add(task)
        flash('Your task has been sent out.')
        return redirect(url_for('.hired', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('workers.html', post=
    post, posts=[post], comments=comments, form=form1, form2=form2, pagination=pagination, tasks=tasks, apps=apps)

@main.route('/studenthired/<int:id>', methods=['GET', 'POST'])
@login_required
def studenthired(id):
    post = Post.query.get_or_404(id)
    apps = Application.query.filter_by(post_id=id, approved=True)
    tasks = Task.query.filter_by(post_id=id, worker_id=current_user.id)
    form1 = CommentForm(prefix="form1")
    if form1.validate_on_submit():
        comment = Comment(body=form1.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your message has been sent.')
        return redirect(url_for('.studenthired', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('studentworkers.html', post=
    post, posts=[post], comments=comments, form=form1, pagination=pagination, tasks=tasks, apps=apps)

@main.route('/completetask/<int:id>/<int:postid>', methods=['GET', 'POST'])
def completetask(id, postid):
    task = Task.query.get_or_404(id)
    task.done = True
    flash("Task Completed")
    return redirect(url_for('.studenthired', id=postid))

@main.route('/approve/<int:id>/<int:applicant_id>', methods=['GET', 'POST'])
def approve(id, applicant_id):
    app = Application.query.filter_by(post_id=id, applicant_id=applicant_id).first()
    post = Post.query.get_or_404(id)
    app.approved = True
    app_count = post.applicant_count
    app_count = int(app_count) - 1
    post.applicant_count = app_count
    post_workers = post.workers
    post_workers = post.workers + 1
    post.workers = post_workers
    flash('Applicant ' + app.applicant.username + ' approved')
    return redirect(url_for('.post', id=id))

@main.route('/reject/<int:id>/<int:applicant_id>', methods=['GET', 'POST'])
def reject(id, applicant_id):
    app = Application.query.filter_by(post_id=id, applicant_id=applicant_id).first()
    post = Post.query.get_or_404(id)
    app_count = post.applicant_count
    app_count = int(app_count) - 1
    post.applicant_count = app_count
    db.session.delete(app)
    flash('Applicant ' + app.applicant.username + ' deleted')
    return redirect(url_for('.post', id=id))

@main.route('/job_completed/<int:id>', methods=['GET', 'POST'])
def job_completed(id):
    post = Post.query.get_or_404(id)
    post.job_completed = True
    flash('Job completed')
    return redirect(url_for('.company', username=current_user.username))

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    apps = Application.query.filter_by(applicant_id=user.id, approved=True)
    page = request.args.get('page', 1, type=int)
    posts = Post.query.all()
    return render_template('user.html', user=user, posts=posts, apps=apps)

@main.route('/company/<username>')
def company(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    apps = Application.query.all()
    return render_template('company-profile.html', user=user, posts=posts, apps=apps,
                          pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.university = form.university.data
        current_user.year = form.year.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.university.data = current_user.university
    form.year.data = current_user.year
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-company-profile', methods=['GET', 'POST'])
@login_required
def edit_company_profile():
    form = EditCompanyProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.industry = form.industry.data
        current_user.website = form.website.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.company', username=current_user.username))
    form.name.data = current_user.name
    form.industry.data = current_user.industry
    form.website.data = current_user.website
    form.about_me.data = current_user.about_me
    return render_template('edit_company_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', post=post, posts=[post])


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))
