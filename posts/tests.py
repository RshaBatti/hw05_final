from re import U

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from .models import Post, Group, Follow, Comment
from django.core.cache import cache


class TestUserScript(TestCase):
    def setUp(self):
        self.auth_user = User.objects.create_user(username="kotok",
                                                  email="kotok@snow.com",
                                                  password="54321")
        self.auth_user_2 = User.objects.create(username="kotokok",
                                               email="kotokok@snow.com",
                                               password="54321")
        self.auth_client = Client()
        self.no_auth_client = Client()
        self.auth_client.force_login(self.auth_user)

        self.group = Group.objects.create(title='test_group',
                                          slug='test_group',
                                          description='test_description', )
        self.test_text = 'test_text'

    def get_urls(self, post):
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.auth_user.username}),
            reverse('post', kwargs={'username': self.auth_user.username,
                                    'post_id': post.id}),
            reverse('groups', kwargs={'slug': self.group.slug})
        ]
        return urls

    def check_post_on_page(self, url, post):
        response = self.auth_client.get(url)
        if 'paginator' in response.context:
            posts_list = response.context['paginator'].object_list[0]
            self.assertEqual(posts_list.text, post.text)
            self.assertEqual(posts_list.author, post.author)
            self.assertEqual(posts_list.group, post.group)
        else:
            self.assertEqual(response.context['post'], post)

    def test_profile(self):
        response = self.auth_client.get(
            reverse('profile', kwargs={'username': self.auth_user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(response.context["author"].username,
                         self.auth_user.username)

    def test_new_post(self):
        response = self.auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk})

        posts = Post.objects.filter(text=self.test_text)
        self.assertNotEqual(posts.count(), 0)
        self.assertEqual(posts.count(), 1)

        post = Post.objects.all()[0]
        self.assertEqual(post.author, self.auth_user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.text, self.test_text)

        self.assertEqual(response.status_code, 302)

    def test_no_auth_user_cant_publish_post(self):
        response = self.no_auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk
        })

        posts = Post.objects.filter(text=self.test_text)
        self.assertFalse(posts)
        login = reverse("login")
        new = reverse("new_post")
        self.assertRedirects(response, f"{login}?next={new}")

    def test_post_publication(self):
        self.auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk
        })
        cache.clear()
        post = Post.objects.get(id=1)
        urls = self.get_urls(post=post)
        for url in urls:
            self.check_post_on_page(url=url, post=post)

    def test_edit_post(self):
        self.auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk})

        post = Post.objects.get(text=self.test_text)

        new_text = 'new_text'
        self.auth_client.post(reverse('post_edit', kwargs={
            'username': self.auth_user.username, 'post_id': post.id}),
                              data={'text': new_text,
                                    'group': self.group.id})
        cache.clear()
        new_post = Post.objects.get(text=new_text)

        urls = self.get_urls(post=new_post)
        for url in urls:
            self.check_post_on_page(url=url, post=new_post)

    def test_error_404(self):
        page = 'not_create_page'
        response = self.auth_client.get(page)
        self.assertEqual(response.status_code, 404)

    def test_create_post_with_img(self):
        with open('posts/media/file.jpg', 'rb') as img:
            post = self.auth_client.post(reverse('new_post'), data={
                'text': self.test_text,
                'group': self.group.pk,
                'image': img}, follow=True)
        cache.clear()
        self.assertEqual(post.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)

        create_post = Post.objects.get(text=self.test_text)
        urls = self.get_urls(post=create_post)
        for url in urls:
            response = self.auth_client.get(url)
            self.assertEqual(post.status_code, 200)
            self.assertContains(response, '<img')

    def test_create_post_with_no_grap_file(self):
        with open('posts/media/file.txt', 'rb') as img:
            post = self.auth_client.post(reverse('new_post'), data={
                'text': self.test_text,
                'group': self.group.pk,
                'image': img}, follow=True)
        self.assertEqual(post.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_follow_unfollow(self):
        self.auth_client.post(reverse('profile_follow',
                                      kwargs={
                                          'username': self.auth_user_2.username}),
                              data={'user': self.auth_user.username,
                                    'author': self.auth_user_2.username})
        follow = Follow.objects.filter(author=self.auth_user_2,
                                       user=self.auth_user)
        self.assertEqual(follow.count(), 1)

        self.auth_client.post(reverse('profile_unfollow',
                                      kwargs={
                                          'username': self.auth_user_2.username}),
                              data={'user': self.auth_user.username,
                                    'author': self.auth_user_2.username})
        self.assertEqual(follow.count(), 0)

    def test_follow_index(self):
        self.auth_client.post(reverse('profile_follow',
                                      kwargs={
                                          'username': self.auth_user_2.username}),
                              data={'user': self.auth_user.username,
                                    'author': self.auth_user_2.username})
        self.auth_client.force_login(self.auth_user_2)
        self.auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk})
        post_follow = Post.objects.all()[0]
        response = self.auth_client.get(reverse('follow_index'))
        self.assertNotContains(response, 'test_text')

        self.auth_client.force_login(self.auth_user)
        response = self.auth_client.get(reverse('follow_index'))
        posts_list = response.context['paginator'].object_list[0]
        self.assertEqual(posts_list.text, post_follow.text)

    def test_no_auth_user_comment(self):
        self.auth_client.post(reverse('new_post'), data={
            'text': self.test_text,
            'group': self.group.pk})
        new_post = Post.objects.get(text=self.test_text)
        self.auth_client.post(
            reverse('add_comment',
                    kwargs={'username': self.auth_user.username,
                            'post_id': new_post.id}),
            data={'text': 'comment_text'})
        response = self.auth_client.get(
            reverse('post',
                    kwargs={'username': self.auth_user.username,
                            'post_id': new_post.id}))
        self.assertContains(response, 'comment_text')

        self.no_auth_client.post(
            reverse('add_comment',
                    kwargs={'username': self.auth_user.username,
                            'post_id': new_post.id}),
            data={'text': 'new_comment'})
        response = self.auth_client.get(
            reverse('post',
                    kwargs={'username': self.auth_user.username,
                            'post_id': new_post.id}))
        self.assertNotContains(response, 'new_comment')
